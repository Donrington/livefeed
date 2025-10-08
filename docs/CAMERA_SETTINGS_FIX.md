# Camera Settings Error Fix

## Problem

When testing the camera settings implementation, two issues occurred:

### 1. JavaScript Blob Error
```
Error parsing WebSocket message: SyntaxError: Unexpected token 'o', "[object Blob]" is not valid JSON
```

**Cause:** Django was sending **binary protobuf data** back to the browser, but JavaScript expected JSON.

**Why it happened:** Both the Pi AND the browser connect to the same WebSocket endpoint (`/ws/camera/`), so Django couldn't distinguish between them. When the browser sent a setting change, Django would broadcast the response as protobuf to ALL connections, including back to the browser.

### 2. Camera Settings Not Applied
The Pi wasn't receiving the camera setting commands from the browser.

## Solution

Updated the Django consumer to **track which connection is from the Pi vs the browser**, and route messages appropriately:

### Changes Made in `consumers.py`

#### 1. Added Connection Tracking (line 16)
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.is_pi_connection = False  # Track if this is Pi or browser
```

#### 2. Mark Pi Connection on First Protobuf (line 44)
```python
if bytes_data:
    # Mark this connection as coming from Pi
    self.is_pi_connection = True
```

When we receive binary protobuf data, we know it's from the Pi (browsers only send JSON).

#### 3. Broadcast Camera Status to Browsers Only (lines 71-97)
```python
async def broadcast_camera_status(self, cam_data):
    """Broadcast camera status to all browser clients via channel layer"""
    await self.channel_layer.group_send(
        self.group_name,
        {
            'type': 'camera_status_update',
            'isConnected': cam_data.isConnected,
            'brightness': cam_data.brightness,
            'contrast': cam_data.contrast,
            'exposure': cam_data.exposure,
            'focus': cam_data.focus,
        }
    )

async def camera_status_update(self, event):
    """Handler for camera_status_update group messages - sends JSON to browser"""
    # Only send to browser clients, not to Pi
    if not self.is_pi_connection:
        await self.send(text_data=json.dumps({
            'type': 'camera_status',
            'isConnected': event['isConnected'],
            'brightness': event['brightness'],
            'contrast': event['contrast'],
            'exposure': event['exposure'],
            'focus': event['focus'],
        }))
```

Now camera status is sent as **JSON to browsers only**, never back to the Pi.

#### 4. Forward Settings to Pi Only (lines 99-129)
```python
async def send_setting_to_pi(self, setting: str, value: int):
    """Send camera setting command to Pi via channel layer"""
    await self.channel_layer.group_send(
        self.group_name,
        {
            'type': 'forward_setting_to_pi',
            'setting': setting,
            'value': value,
        }
    )

async def forward_setting_to_pi(self, event):
    """Handler for forward_setting_to_pi - sends protobuf to Pi only"""
    # Only send to Pi connection, not to browsers
    if self.is_pi_connection:
        cmd = messages_pb2.CameraSettingsCommand()
        cmd.setting = event['setting']
        cmd.value = event['value']
        await self.send(bytes_data=cmd.SerializeToString())
```

Now setting commands are sent as **protobuf to Pi only**, never to browsers.

## How It Works Now

### Flow 1: Browser → Pi (Setting Change)
1. User moves slider in browser
2. Browser sends JSON: `{type: 'camera_setting', setting: 'brightness', value: 50}`
3. Django broadcasts to group as `forward_setting_to_pi` event
4. **Only Pi connection** receives it and gets protobuf
5. Pi applies setting to camera

### Flow 2: Pi → Browser (Status Update)
1. Pi sends camera status as protobuf
2. Django marks this connection as `is_pi_connection = True`
3. Django broadcasts to group as `camera_status_update` event
4. **Only browser connections** receive it as JSON
5. Browsers update sliders

## Result

✅ **No more Blob errors** - Browsers only receive JSON
✅ **Pi receives commands** - Settings are applied to camera
✅ **Browsers see updates** - Sliders sync with actual camera values

## Files Modified

1. `live_feed/app/consumers.py` - Added connection tracking and message routing
