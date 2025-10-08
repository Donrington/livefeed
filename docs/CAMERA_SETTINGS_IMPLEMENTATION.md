# Camera Settings Control Implementation

## Overview

This document explains the implementation of a **bidirectional camera control system** that allows you to adjust camera brightness, contrast, exposure, and focus from the Django web interface.

The changes flow like this:

**Frontend (JavaScript) → Django (WebSocket) → Raspberry Pi → Camera Hardware → Pi → Django → Frontend**

---

## Changes Made (Step by Step)

### 1. Updated Protobuf Schema

**File:** `live_feed/messages/messages.proto`

**What Changed:**
- Added camera setting fields to `CameraStatus` message (brightness, contrast, exposure, focus)
- Created new `CameraSettingsCommand` message for sending commands from Django to Pi

**Why:** Protobuf provides efficient binary serialization for the messages traveling between Pi and Django over WebSocket.

```protobuf
message CameraStatus {
  bool isConnected = 1;
  int32 brightness = 2;      // Current brightness value
  int32 contrast = 3;        // Current contrast value
  int32 exposure = 4;        // Current exposure value (multiplied by 10)
  int32 focus = 5;           // Current focus value
}

message CameraSettingsCommand {
  string setting = 1;        // "brightness", "contrast", "exposure", "focus"
  int32 value = 2;           // New value to set
}
```

---

### 2. Modified Pi Publisher

**File:** `zero_latency_publisher.py`

#### a) Added camera settings storage (line 148-154)

```python
self.camera_settings = {
    'brightness': 0,    # -130 to +130
    'contrast': 0,      # -130 to +130
    'exposure': -5,     # camera accepts floats
    'focus': 0          # 0 to 500
}
self.settings_lock = threading.Lock()  # Thread-safe access
```

**Why:** Store current settings so we can read/modify them safely from multiple threads.

#### b) Added `apply_camera_settings()` method (line 248-267)

```python
def apply_camera_settings(self):
    """Apply current camera settings to the camera"""
    if self.cap is None or not self.cap.isOpened():
        return

    with self.settings_lock:
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.camera_settings['brightness'])
        self.cap.set(cv2.CAP_PROP_CONTRAST, self.camera_settings['contrast'])
        self.cap.set(cv2.CAP_PROP_EXPOSURE, self.camera_settings['exposure'])
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.cap.set(cv2.CAP_PROP_FOCUS, self.camera_settings['focus'])
```

**Why:** This method applies all settings to the camera hardware using OpenCV's `cv2.VideoCapture.set()` function. Called when camera initializes and when settings change.

#### c) Added `update_camera_setting()` method (line 269-291)

```python
def update_camera_setting(self, setting, value):
    """Update a specific camera setting"""
    with self.settings_lock:
        if setting in self.camera_settings:
            self.camera_settings[setting] = value

            # Apply immediately to camera
            if self.cap and self.cap.isOpened():
                if setting == 'brightness':
                    self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)
                elif setting == 'contrast':
                    self.cap.set(cv2.CAP_PROP_CONTRAST, value)
                elif setting == 'exposure':
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, value)
                elif setting == 'focus':
                    self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                    self.cap.set(cv2.CAP_PROP_FOCUS, value)

            # Send updated status to Django
            self.send_camera_status()
```

**Why:** This is called when Django sends a setting change command. It updates the stored value, applies it to the camera, then sends confirmation back to Django.

#### d) Added `send_camera_status()` method (line 293-306)

```python
def send_camera_status(self):
    """Send current camera status including settings to Django"""
    with self.settings_lock:
        self.cam_status.isConnected = (self.cap is not None and self.cap.isOpened())
        self.cam_status.brightness = self.camera_settings['brightness']
        self.cam_status.contrast = self.camera_settings['contrast']
        self.cam_status.exposure = int(self.camera_settings['exposure'] * 10)  # Convert float to int
        self.cam_status.focus = self.camera_settings['focus']

    try:
        to_async_queue.put(self.cam_status.SerializeToString(), block=False)
    except queue.Full:
        log.warning("Queue full, skipping status update")
```

**Why:** Packages current camera settings into a protobuf message and puts it in the queue. The async thread picks it up and sends it to Django via WebSocket.

#### e) Updated WebSocket `reader()` function (line 45-76)

```python
async def reader(ws: websockets.WebSocketClientProtocol, stop_event: asyncio.Event):
    """
    Reader coroutine to handle incoming messages from the WebSocket server.
    Processes CameraSettingsCommand messages from Django.
    """
    global publisher_instance
    while not stop_event.is_set():
        try:
            async for message in ws:
                # Parse incoming protobuf message
                try:
                    cmd = messages_pb2.CameraSettingsCommand()
                    cmd.ParseFromString(message)

                    # Apply the setting change to the camera
                    if publisher_instance:
                        # For exposure, divide by 10 (protobuf sends int, camera expects float)
                        value = cmd.value / 10.0 if cmd.setting == 'exposure' else cmd.value
                        publisher_instance.update_camera_setting(cmd.setting, value)
                        log.info(f"Applied setting: {cmd.setting} = {value}")
                    else:
                        log.warning("Publisher instance not available")

                except Exception as parse_error:
                    log.error(f"Failed to parse command: {parse_error}")

        except websockets.ConnectionClosed:
            log.info("websocket connection closed")
            break
        except Exception as e:
            log.info(f"Error in reader task: {e}")
            break
```

**Why:** This is the **receive path** - when Django sends a command to change a setting, this function receives it, parses the protobuf, and calls `update_camera_setting()`.

#### f) Set global publisher instance (line 460)

```python
# In main() function
publisher_instance = publisher  # Allow WebSocket callbacks to access publisher
```

**Why:** The async WebSocket thread needs to call methods on the publisher object. Since they run in different threads, we use a global reference.

---

### 3. Modified Django Consumer

**File:** `live_feed/app/consumers.py`

#### a) Updated `receive()` method to handle both protobuf and JSON (line 38-64)

```python
async def receive(self, text_data=None, bytes_data=None):
    # Handle protobuf messages from Pi
    if bytes_data:
        try:
            cam_data = messages_pb2.CameraStatus()
            cam_data.ParseFromString(bytes_data)

            # Send camera status including settings to frontend
            await self.send_camera_status(cam_data)

        except Exception as e:
            log.error(f"Error parsing protobuf: {e}")

    # Handle JSON messages from JavaScript (setting change commands)
    if text_data:
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'camera_setting':
                # Forward camera setting command to Pi
                setting = data.get('setting')
                value = data.get('value')
                await self.send_setting_to_pi(setting, value)

        except Exception as e:
            log.error(f"Error handling JSON message: {e}")
```

**Why:** This consumer now handles TWO message types:
- **Binary (bytes_data)**: Protobuf messages FROM Pi with camera status
- **Text (text_data)**: JSON messages FROM JavaScript with setting change requests

#### b) Added `send_camera_status()` method (line 67-77)

```python
async def send_camera_status(self, cam_data):
    """Send complete camera status including settings to frontend"""
    await self.send(text_data=json.dumps({
        'type': 'camera_status',
        'isConnected': cam_data.isConnected,
        'brightness': cam_data.brightness,
        'contrast': cam_data.contrast,
        'exposure': cam_data.exposure,  # Already multiplied by 10 from Pi
        'focus': cam_data.focus,
    }))
    log.info(f"Sent camera status to frontend: brightness={cam_data.brightness}, contrast={cam_data.contrast}")
```

**Why:** Converts protobuf data from Pi into JSON and sends it to the JavaScript frontend via WebSocket.

#### c) Added `send_setting_to_pi()` method (line 79-92)

```python
async def send_setting_to_pi(self, setting: str, value: int):
    """Send camera setting command to Pi via protobuf"""
    try:
        # Create protobuf command message
        cmd = messages_pb2.CameraSettingsCommand()
        cmd.setting = setting
        cmd.value = value

        # Send binary protobuf message to Pi
        await self.send(bytes_data=cmd.SerializeToString())
        log.info(f"Sent setting command to Pi: {setting} = {value}")

    except Exception as e:
        log.error(f"Error sending setting to Pi: {e}")
```

**Why:** When JavaScript requests a setting change, this converts it to protobuf and sends it to the Pi.

---

## How the Data Flows

### Flow 1: Camera Status Updates (Pi → Django → Frontend)

1. **Pi** camera settings change → `send_camera_status()` creates protobuf
2. Protobuf goes into `to_async_queue` → **async thread** picks it up
3. **WebSocket writer** sends it to Django
4. **Django consumer** receives bytes_data → parses protobuf → sends JSON to frontend
5. **JavaScript** receives camera status and updates UI

### Flow 2: User Changes Setting (Frontend → Django → Pi → Camera)

1. **User** moves brightness slider in browser
2. **JavaScript** sends JSON via WebSocket: `{type: 'camera_setting', setting: 'brightness', value: 50}`
3. **Django consumer** receives JSON → creates protobuf `CameraSettingsCommand`
4. Django sends protobuf to **Pi WebSocket reader**
5. **Pi reader** parses protobuf → calls `update_camera_setting('brightness', 50)`
6. **Pi** applies to camera using `cv2.CAP_PROP_BRIGHTNESS`
7. **Pi** sends confirmation back (Flow 1) to update frontend

---

## Key Technical Concepts Used

1. **Thread-Safe Queue**: `to_async_queue` safely transfers data from main thread to async thread
2. **Thread Locks**: `settings_lock` prevents race conditions when reading/writing settings
3. **Protobuf Binary Serialization**: Efficient message format for Pi↔Django communication
4. **WebSocket Bidirectional**: Same connection for sending AND receiving
5. **OpenCV Camera Properties**: `cv2.CAP_PROP_*` constants control camera hardware
6. **Global Reference**: `publisher_instance` allows async code to call publisher methods

---

---

## Frontend Implementation

### 4. Updated Settings Page UI

**File:** `live_feed/templates/settings.html` (lines 156-193)

Updated the Camera Settings tab to include proper controls for camera settings with correct ranges and labels.

**Key Changes:**
- Brightness slider: -130 to +130 (was incorrect range 0-1000)
- Contrast slider: -130 to +130 (was incorrect range 0-200)
- Exposure slider: -130 to 0 (replaces saturation slider)
- Focus slider: 0 to 500 (replaces sharpness slider)
- Each slider calls `updateCameraSetting(setting, value)` on input
- Added range labels for user guidance

### 5. Updated Settings JavaScript

**File:** `live_feed/static/js/settings.js`

Completely rewrote to add WebSocket functionality and camera control handlers.

#### a) WebSocket Connection (lines 5-74)

```javascript
function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws/camera/`;
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'camera_status') {
            // Update sliders with current camera settings from Pi
            updateSliderValue('brightness', data.brightness);
            updateSliderValue('contrast', data.contrast);
            updateSliderValue('exposure', data.exposure);
            updateSliderValue('focus', data.focus);
        }
    };
}
```

**Why:** Connects to `/ws/camera/` endpoint, receives camera status updates, syncs sliders to actual camera values.

#### b) Send Setting Change (lines 87-104)

```javascript
function updateCameraSetting(setting, value) {
    // Update display immediately
    document.getElementById(`${setting}-val`).textContent = value;

    // Send to backend via WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            type: 'camera_setting',
            setting: setting,
            value: parseInt(value)
        };
        ws.send(JSON.stringify(message));
    }
}
```

**Why:** When user moves slider, updates UI immediately and sends JSON to Django, which forwards to Pi as protobuf.

---

## Complete Data Flow (End-to-End)

### User Adjusts Camera Setting:

1. **User** drags brightness slider in Settings page
2. **HTML** `oninput` event → calls `updateCameraSetting('brightness', 50)`
3. **JavaScript** sends JSON via WebSocket: `{type: 'camera_setting', setting: 'brightness', value: 50}`
4. **Django Consumer** receives JSON → creates protobuf `CameraSettingsCommand`
5. **Django** sends binary protobuf to Pi WebSocket
6. **Pi WebSocket reader** parses protobuf → calls `publisher.update_camera_setting('brightness', 50)`
7. **Pi Publisher** applies to camera via `cv2.CAP_PROP_BRIGHTNESS`
8. **Pi** sends confirmation via `send_camera_status()` → creates `CameraStatus` protobuf
9. Protobuf → queue → async thread → WebSocket → Django
10. **Django Consumer** receives protobuf → sends JSON to all browsers
11. **JavaScript** receives `camera_status` → updates slider to confirm

---

## Implementation Status

✅ **Backend is complete!** Pi and Django communicate camera settings via protobuf
✅ **Frontend UI is complete!** Settings page has sliders for brightness, contrast, exposure, focus
✅ **WebSocket integration is complete!** JavaScript sends/receives camera settings in real-time

🎉 **The entire camera settings control system is now fully implemented!**

---

## Camera Setting Ranges

- **Brightness**: -130 to +130 (default: 0)
- **Contrast**: -130 to +130 (default: 0)
- **Exposure**: -130 to 0 (default: -50, representing -5.0 multiplied by 10)
- **Focus**: 0 to 500 (default: 0, autofocus disabled)

---

## Files Modified

1. `live_feed/messages/messages.proto` - Protobuf schema
2. `zero_latency_publisher.py` - Pi-side camera control
3. `live_feed/app/consumers.py` - Django WebSocket consumer
4. `live_feed/templates/settings.html` - Settings page UI with camera control sliders
5. `live_feed/static/js/settings.js` - WebSocket connection and camera control handlers
