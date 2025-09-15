# Zero Latency Live Feed

A streamlined live video streaming system using MediaMTX, OpenCV, and Django.

## Core Files

- **`zero_latency_publisher.py`** - Camera capture and stream publisher (auto-starts MediaMTX)
- **`zero_latency_receiver.py`** - Stream receiver with display window
- **`live_feed/`** - Django web interface for viewing HLS stream

## Quick Start

1. **Start Publisher:**
   ```bash
   python zero_latency_publisher.py --mediamtx-path "path/to/mediamtx.exe"
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

## Publisher Usage

### Basic Usage
```bash
python zero_latency_publisher.py --mediamtx-path "C:\path\to\mediamtx.exe"
```
example 
```bash
cd ~/Desktop/livefeed
source opencv-env/bin/activate
python3 zero_latency_publisher.py --mediamtx-path /home/nextgen/Desktop/mediamtx
```
### Command Line Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--mediamtx-path` | `-m` | string | **Required** | Path to MediaMTX executable |
| `--camera-index` | `-c` | int | 0 | Camera index to use |
| `--width` | `-w` | int | 640 | Video width resolution |
| `--height` | `-ht` | int | 480 | Video height resolution |
| `--fps` | `-f` | int | 30 | Target frames per second |
| `--bitrate` | `-b` | string | 800k | Video bitrate (e.g., 800k, 1M) |
| `--rtsp-url` | `-u` | string | rtsp://localhost:8554/zerolatency | RTSP stream URL |

### Examples

**Basic usage with custom MediaMTX path:**
```bash
python zero_latency_publisher.py -m "C:\tools\mediamtx\mediamtx.exe"
```

**High resolution with custom settings:**
```bash
python zero_latency_publisher.py \
  --mediamtx-path "C:\tools\mediamtx\mediamtx.exe" \
  --width 1280 \
  --height 720 \
  --fps 60 \
  --bitrate 2M
```

**Using different camera and stream URL:**
```bash
python zero_latency_publisher.py \
  -m "C:\tools\mediamtx\mediamtx.exe" \
  -c 1 \
  -u "rtsp://localhost:8554/mycamera"
```

**Get help:**
```bash
python zero_latency_publisher.py --help
```

## MediaMTX Setup

1. Download MediaMTX from: https://github.com/bluenviron/mediamtx/releases
2. Extract to any directory on your system
3. Use the `--mediamtx-path` argument to point to the executable

The publisher automatically manages MediaMTX startup/shutdow