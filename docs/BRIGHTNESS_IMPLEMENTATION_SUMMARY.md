# Brightness Control Implementation Summary

## Overview
Implemented real-time camera brightness control using the same thread-based async messaging pattern as FPS counter.

---

## How It Works (Same as FPS)

### FPS Flow:
```
Pi counts frames → Sends FPS via protobuf → Django → Browser displays
```

### Brightness Flow (Same Pattern):
```
User moves slider → Browser sends JSON → Django converts to protobuf
→ Pi applies to camera → Pi sends confirmation → Browser updates
```

---

## Understanding the Example Code

Your reference code (`camera_control_example.py`) showed:
```python
brightness = 0  # -130 (dark) to +130 (bright)
vid = cv2.VideoCapture(camera_id)

# When user presses 'B' key
if key == ord('B'):
    brightness += 10
    vid.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
```

**Key Concept:** Use `cv2.CAP_PROP_BRIGHTNESS` to control camera hardware.

We adapted this to work over WebSocket with protobuf messaging instead of keyboard input.

---

## Files Modified & Code Sections

### 1. **Protobuf Schema**
**File:** `live_feed/messages/messages.proto`
**Lines:** 1-16

```protobuf
message CameraStatus {
  bool isConnected = 1;
  int32 brightness = 2;    // NEW: Camera brightness value
  float fps = 3;           // Existing FPS field
}

message CameraSettingsCommand {
  string setting = 1;      // NEW: "brightness"
  int32 value = 2;         // NEW: Value to set
}
```

**What it does:** Defines message format for Pi ↔ Django communication.

---

### 2. **Pi Publisher - Storage & Initialization**
**File:** `zero_latency_publisher.py`
**Lines:** 164-168

```python
""" Initialize camera settings with default values."""
self.camera_settings = {
    'brightness': 0,    # -130 to +130
}
self.settings_lock = threading.Lock()  # Thread-safe access
```

**What it does:** Stores current brightness value safely across threads.

---

### 3. **Pi Publisher - Apply Settings to Camera**
**File:** `zero_latency_publisher.py`
**Lines:** 262-291 (apply_camera_settings)

```python
def apply_camera_settings(self):
    """Apply current camera settings to the camera"""
    with self.settings_lock:
        # Get current brightness
        current = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

        # Set new brightness (from your example code)
        result = self.cap.set(cv2.CAP_PROP_BRIGHTNESS,
                             self.camera_settings['brightness'])

        # Verify it was set
        actual = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
        log.info(f"Brightness: requested={value}, actual={actual}")
```

**What it does:** Uses `cv2.CAP_PROP_BRIGHTNESS` (from your example) to actually change camera hardware.

---

### 4. **Pi Publisher - Update Settings (When User Changes)**
**File:** `zero_latency_publisher.py`
**Lines:** 293-307 (update_camera_setting)

```python
def update_camera_setting(self, setting, value):
    """Update a specific camera setting"""
    with self.settings_lock:
        if setting == 'brightness':
            self.camera_settings[setting] = value

            # Apply to camera immediately
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

            log.info(f"Applied brightness = {value}")
```

**What it does:** Called when Django sends brightness change command from browser.

---

### 5. **Pi Publisher - Send Status to Django**
**File:** `zero_latency_publisher.py`
**Lines:** 309-318 (send_camera_status)

```python
def send_camera_status(self):
    """Send current camera status including settings to Django"""
    with self.settings_lock:
        self.cam_status.isConnected = (self.cap is not None)
        self.cam_status.brightness = self.camera_settings['brightness']
        self.cam_status.fps = self.current_fps

    # Put in queue for async thread to send
    to_async_queue.put(self.cam_status.SerializeToString(), block=False)
```

**What it does:** Packages brightness + fps into protobuf and queues for WebSocket send (same as FPS).

---

### 6. **Pi Publisher - Main Loop (Send on Every Frame)**
**File:** `zero_latency_publisher.py`
**Lines:** 364-373

```python
while self.isRunning():
    ret, frame = self.cap.read()

    # Update camera status with current settings
    with self.settings_lock:
        self.cam_status.isConnected = ret
        self.cam_status.brightness = self.camera_settings['brightness']
        self.cam_status.fps = self.current_fps

    # Send to Django (same as FPS sending)
    to_async_queue.put(self.cam_status.SerializeToString())
```

**What it does:** Sends brightness + fps on every frame (same pattern as FPS).

---

### 7. **Pi WebSocket Reader - Receive Commands**
**File:** `zero_latency_publisher.py`
**Lines:** 45-76 (reader function)

```python
async def reader(ws: websockets.WebSocketClientProtocol, stop_event: asyncio.Event):
    """Reader coroutine to handle incoming messages from Django"""
    global publisher_instance

    async for message in ws:
        # Parse protobuf command from Django
        cmd = messages_pb2.CameraSettingsCommand()
        cmd.ParseFromString(message)

        # Apply the setting change
        if publisher_instance:
            publisher_instance.update_camera_setting(cmd.setting, cmd.value)
            log.info(f"Applied setting: {cmd.setting} = {cmd.value}")
```

**What it does:** Receives brightness commands from Django via WebSocket and applies them.

---

### 8. **Django Consumer - Receive from Pi**
**File:** `live_feed/app/consumers.py`
**Lines:** 39-53 (receive method - bytes_data part)

```python
async def receive(self, text_data=None, bytes_data=None):
    # Handle protobuf messages from Pi
    if bytes_data:
        # Mark this connection as coming from Pi
        self.is_pi_connection = True

        cam_data = messages_pb2.CameraStatus()
        cam_data.ParseFromString(bytes_data)

        # Send camera status to ALL browser clients
        await self.broadcast_camera_status(cam_data)
```

**What it does:** Receives brightness + fps from Pi, forwards to browsers.

---

### 9. **Django Consumer - Receive from Browser**
**File:** `live_feed/app/consumers.py`
**Lines:** 55-68 (receive method - text_data part)

```python
# Handle JSON messages from JavaScript (setting change commands)
if text_data:
    data = json.loads(text_data)

    if data.get('type') == 'camera_setting':
        # Forward camera setting command to Pi only
        setting = data.get('setting')
        value = data.get('value')
        await self.send_setting_to_pi(setting, value)
```

**What it does:** Receives brightness change from browser, forwards to Pi.

---

### 10. **Django Consumer - Broadcast to Browsers**
**File:** `live_feed/app/consumers.py`
**Lines:** 71-81 (broadcast_camera_status)

```python
async def broadcast_camera_status(self, cam_data):
    """Broadcast camera status to all browser clients"""
    await self.channel_layer.group_send(
        self.group_name,
        {
            'type': 'camera_status_update',
            'isConnected': cam_data.isConnected,
            'brightness': cam_data.brightness,
            'fps': cam_data.fps,
        }
    )
```

**What it does:** Sends brightness + fps to all connected browsers.

---

### 11. **Django Consumer - Send Commands to Pi**
**File:** `live_feed/app/consumers.py`
**Lines:** 102-129 (send_setting_to_pi & forward_setting_to_pi)

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
    """Handler - sends protobuf to Pi only"""
    if self.is_pi_connection:
        cmd = messages_pb2.CameraSettingsCommand()
        cmd.setting = event['setting']
        cmd.value = event['value']

        # Send binary protobuf to Pi
        await self.send(bytes_data=cmd.SerializeToString())
```

**What it does:** Converts JSON from browser to protobuf for Pi.

---

### 12. **Settings Page UI**
**File:** `live_feed/templates/settings.html`
**Lines:** 158-166

```html
<div>
    <label class="block text-sm text-slate-400 mb-2">
        Brightness: <span id="brightness-val">0</span>
    </label>
    <input type="range"
           id="brightness-slider"
           class="w-full"
           min="-130"
           max="130"
           value="0"
           oninput="updateCameraSetting('brightness', this.value)">
    <div class="flex justify-between text-xs text-slate-500 mt-1">
        <span>-130 (Dark)</span>
        <span>0 (Default)</span>
        <span>130 (Bright)</span>
    </div>
</div>
```

**What it does:** Slider that user moves to change brightness.

---

### 13. **Settings Page JavaScript - WebSocket Setup**
**File:** `live_feed/static/js/settings.js`
**Lines:** 33-59 (connectWebSocket function)

```javascript
function connectWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws/camera/`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('✅ Settings WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'camera_status') {
            // Update slider with current camera setting from Pi
            updateSliderValue('brightness', data.brightness);
        }
    };
}
```

**What it does:** Connects to Django WebSocket, receives brightness updates.

---

### 14. **Settings Page JavaScript - Send Brightness Change**
**File:** `live_feed/static/js/settings.js`
**Lines:** 87-104 (updateCameraSetting function)

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
        console.log(`📤 Sent ${setting} = ${value}`);
    }
}
```

**What it does:** Called when user moves slider, sends JSON to Django.

---

### 15. **Dashboard JavaScript - Display Updates**
**File:** `live_feed/static/js/dashboard.js`
**Lines:** 304-321 (handleCameraStatus function)

```javascript
function handleCameraStatus(message) {
    // Update FPS display
    if (typeof message.fps !== 'undefined') {
        document.getElementById('fps-display').textContent = message.fps.toFixed(1);
    }

    // Update brightness if needed
    const brightnessSlider = document.getElementById('camera-brightness-slider');
    if (brightnessSlider && typeof message.brightness !== 'undefined') {
        brightnessSlider.value = message.brightness;
    }
}
```

**What it does:** Updates dashboard when brightness changes (if dashboard has brightness display).

---

## Data Flow Summary

```
┌─────────────┐
│   Browser   │ User moves slider
│  (Settings) │
└──────┬──────┘
       │ JSON: {type: 'camera_setting', setting: 'brightness', value: 50}
       ↓
┌──────────────┐
│    Django    │ WebSocket Consumer
│  (consumers) │
└──────┬───────┘
       │ Protobuf: CameraSettingsCommand {setting: 'brightness', value: 50}
       ↓
┌──────────────┐
│  Pi (Python) │ WebSocket Reader
│  (publisher) │
└──────┬───────┘
       │ cv2.CAP_PROP_BRIGHTNESS
       ↓
┌──────────────┐
│   Camera     │ Hardware brightness changes
│  (Hardware)  │
└──────┬───────┘
       │ Confirmation
       ↓
┌──────────────┐
│  Pi (Python) │ Sends status back
│  (publisher) │
└──────┬───────┘
       │ Protobuf: CameraStatus {brightness: 50, fps: 30.0}
       ↓
┌──────────────┐
│    Django    │ Forwards to browser
│  (consumers) │
└──────┬───────┘
       │ JSON: {type: 'camera_status', brightness: 50, fps: 30.0}
       ↓
┌──────────────┐
│   Browser    │ Updates slider & FPS
│  (Settings)  │
└──────────────┘
```

---

## Current Issue

**Symptom:** Camera goes dark and won't revert back.

**Logs Show:**
```
Broadcasting setting command: brightness = -2   ← Django side ✓
Forwarded to Pi: brightness = -2                ← Django side ✓
```

**Missing on Pi Side:**
```
Requested brightness: -2                         ← Should appear ✗
Current brightness before set: X                 ← Should appear ✗
Brightness after set: requested=-2, actual=Y     ← Should appear ✗
```

**Diagnosis:** Commands reach Django but Pi isn't processing them.

**Possible causes:**
1. Pi WebSocket reader not receiving messages
2. `publisher_instance` is None
3. Camera doesn't support the brightness values being sent

**Next Step:** Check Pi terminal for brightness logs when slider moves.
