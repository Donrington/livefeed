# Zero Latency Live Feed

A streamlined live video streaming system using MediaMTX, OpenCV, and Django.

## Core Files

- **`zero_latency_publisher.py`** - Camera capture and stream publisher (auto-starts MediaMTX)
- **`zero_latency_receiver.py`** - Stream receiver with display window
- **`live_feed/`** - Django web interface for viewing HLS stream

## Quick Start

1. **Start Publisher:**
   ```bash
   python zero_latency_publisher.py
   ```
   (Automatically starts MediaMTX if not running)

2. **Start Receiver (optional):**
   ```bash
   python zero_latency_receiver.py
   ```

3. **View Web Interface:**
   ```bash
   cd live_feed
   python manage.py runserver
   ```
   Open: http://localhost:8000

## Stream URLs

- **HLS:** http://localhost:8888/zerolatency/index.m3u8
- **RTSP:** rtsp://localhost:8554/zerolatency  
- **WebRTC:** http://localhost:8889/zerolatency

## Dependencies

```bash
pip install -r requirements.txt
```

## MediaMTX

Requires MediaMTX executable at:
`C:\Users\Windows\Desktop\MyProjects\mediamtx\mediamtx.exe`

The publisher automatically manages MediaMTX startup/shutdown.