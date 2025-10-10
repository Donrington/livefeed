# Thread Communication - Simple Explanation

## The Problem
Your Python program has **2 threads running at the same time**:
1. **Main Thread** - Captures camera frames (blocking/synchronous)
2. **Async Thread** - Handles WebSocket communication (non-blocking/asynchronous)

They need to talk to each other safely!

---

## The Solution: Queue

Think of a **queue** like a mailbox between threads.

```python
import queue

# Create a shared mailbox (thread-safe)
to_async_queue = queue.Queue(maxsize=2)
```

---

## How It Works

### Main Thread → Async Thread (Sending Data)

**Main Thread** (Camera Loop):
```python
# Every frame, put brightness + fps into the mailbox
while self.isRunning():
    ret, frame = self.cap.read()

    # Package data into protobuf
    self.cam_status.brightness = self.camera_settings['brightness']
    self.cam_status.fps = self.current_fps

    # Put in mailbox for async thread
    to_async_queue.put(self.cam_status.SerializeToString())

    # Continue capturing frames...
```

**Async Thread** (WebSocket):
```python
async def writer(ws):
    while True:
        try:
            # Check mailbox for new messages
            msg = to_async_queue.get_nowait()

            # Send to Django via WebSocket
            await ws.send(msg)
        except queue.Empty:
            # Mailbox empty, wait a bit
            await asyncio.sleep(0.01)
```

---

### Async Thread → Main Thread (Receiving Commands)

**Async Thread** (WebSocket Reader):
```python
async def reader(ws):
    async for message in ws:
        # Received brightness command from Django
        cmd = messages_pb2.CameraSettingsCommand()
        cmd.ParseFromString(message)

        # Call main thread's function directly
        # (Safe because we use locks inside)
        publisher_instance.update_camera_setting(cmd.setting, cmd.value)
```

**Main Thread** (Publisher):
```python
def update_camera_setting(self, setting, value):
    # Lock prevents both threads from accessing at same time
    with self.settings_lock:
        self.camera_settings[setting] = value
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)
```

---

## Why Locks?

**Problem:** Both threads accessing `self.camera_settings` at the same time = **race condition** (chaos!)

**Solution:** Lock = "Only one thread can enter at a time"

```python
# Create lock
self.settings_lock = threading.Lock()

# Use lock when accessing shared data
with self.settings_lock:
    # Only one thread can be here at a time
    self.camera_settings['brightness'] = value
```

---

## Visual Summary

```
┌─────────────────────┐
│   MAIN THREAD       │
│  (Camera Capture)   │
└──────┬──────────────┘
       │
       │ to_async_queue.put(msg)
       ↓
┌─────────────────────┐
│   QUEUE (Mailbox)   │  ← Thread-safe communication
│   [msg1, msg2]      │
└──────┬──────────────┘
       │
       │ msg = queue.get()
       ↓
┌─────────────────────┐
│   ASYNC THREAD      │
│  (WebSocket)        │
└─────────────────────┘

       ↑ Commands come back ↑

       publisher_instance.update_setting()
       (protected by lock)
```

---

## Key Points

1. **Queue** = Thread-safe mailbox for sending messages
2. **Lock** = Prevents two threads from modifying same data simultaneously
3. **Main Thread** sends status via queue
4. **Async Thread** receives commands and calls functions (protected by locks)

**Result:** Threads can communicate safely without crashing! 🎉
