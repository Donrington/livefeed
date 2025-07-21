# 🎥 Zero Latency Live Streaming System

## What We Built - Simple & Direct

A clean, lightweight live streaming system that:
1. **Captures video** from your webcam 📹
2. **Streams it live** with ultra-low latency 🚀
3. **Measures the delay** in real-time ⏱️
4. **Shows a web dashboard** for monitoring 📊

---

## 🏗️ The Two Main Components

### 1. 📤 Zero Latency Publisher (`zero_latency_publisher.py`)
**What it does:** Captures and streams video directly
- Grabs frames from webcam
- Adds timestamp overlay for latency tracking
- Streams directly to MediaMTX via RTSP
- Uses libx264 software encoding for compatibility

### 2. 📥 Zero Latency Receiver (`zero_latency_receiver.py`)
**What it does:** Receives stream and calculates latency
- Connects to RTSP stream
- Displays video with receiver timestamp
- Calculates dynamic latency in real-time
- Shows FPS and latency metrics on overlay

### 3. 🌐 Django Web Interface
**What it does:** Simple web monitoring
- Displays the live stream in browser
- Connected via MediaMTX HLS output
- Minimal overhead, just for viewing

---

## 🚀 How It Works

```
[Webcam] → [Publisher] → [MediaMTX] → [Web Browser]
                              ↓
                         [Receiver] (for latency measurement)
```

### Simple Data Flow:
1. Publisher captures frame and adds timestamp
2. Streams directly to MediaMTX via RTSP
3. MediaMTX converts to web-friendly HLS
4. Receiver monitors stream and calculates latency
5. Web interface displays the stream

---

## 📁 Project Structure

```
livefeed/
├── zero_latency_publisher.py    # Webcam capture & streaming
├── zero_latency_receiver.py     # Stream monitoring & latency calc
├── live_feed/                   # Django web interface
│   ├── manage.py
│   ├── app/
│   │   ├── models.py           # Database for metrics
│   │   ├── views.py            # Web views
│   │   └── urls.py
│   └── templates/
│       └── live_feed.html      # Web streaming template
└── config/                     # MediaMTX configuration
```

---

## ⚙️ MediaMTX Configuration

MediaMTX handles the streaming server functionality:

```yaml
hls: yes
hlsAddress: :8888
hlsVariant: lowLatency
hlsSegmentDuration: 200ms
hlsPartDuration: 50ms
```

This provides the RTSP-to-HLS conversion for web viewing.

---

## 🏃‍♂️ Quick Start

### 1. Start MediaMTX
```bash
mediamtx.exe
```

### 2. Start Publisher (in one terminal)
```bash
python zero_latency_publisher.py
```

### 3. Start Receiver (in another terminal) 
```bash
python zero_latency_receiver.py
```

### 4. Optional: Start Web Interface
```bash
cd live_feed
python manage.py runserver
```
Then visit: `http://localhost:8000`

---

## 📊 What You'll See

### Publisher Window:
- Live webcam feed
- Green overlay with:
  - `PUB: HH:MM:SS.mmm` (capture timestamp)
  - `FPS: XX.X` (capture framerate)
  - `LAT: XX.Xms` (processing latency)

### Receiver Window:
- Same stream received via RTSP
- Red overlay with:
  - `REC: HH:MM:SS.mmm` (receive timestamp)
  - `REC FPS: XX.X` (receive framerate)
  - `LAT: XX.Xms` (end-to-end latency)

### Web Interface:
- Clean HTML5 video player
- Shows the live stream in browser
- Minimal UI for monitoring

---

## 🔧 Key Features

### Ultra-Low Latency Design:
- Direct RTSP streaming (no intermediate processing)
- Minimal buffering (`buffersize = 1`)
- Software encoding with `ultrafast` + `zerolatency` presets
- Real-time latency calculation and display

### Simple & Clean Code:
- No complex inheritance or modules
- Direct error handling
- Focused functionality
- Easy to understand and modify

### Real-Time Metrics:
- Dynamic latency calculation
- FPS monitoring on both ends
- Visual overlay for immediate feedback

---

## 🎯 Typical Performance

- **End-to-end latency:** 50-200ms
- **Streaming latency:** 30-100ms  
- **Processing overhead:** <20ms
- **Target FPS:** 30fps at 640x480

---

## 🐛 Troubleshooting

### "MediaMTX not running"
Start MediaMTX first: `mediamtx.exe`

### "Cannot open camera"
Close other camera applications (Zoom, Skype, etc.)

### "FFmpeg error"
Ensure FFmpeg is installed and in PATH

### High latency
- Check network connection
- Reduce video resolution in publisher
- Verify MediaMTX is running locally

---

## 🚀 Next Steps

### Easy Improvements:
1. **Adjust resolution:** Change `width/height` in publisher
2. **Modify bitrate:** Adjust `bitrate` setting for quality/speed trade-off
3. **Add recording:** Extend publisher to save video files
4. **Multiple cameras:** Create multiple publisher instances

### Advanced Features:
1. **Hardware encoding:** Add NVENC/QSV support back
2. **Web controls:** Add start/stop buttons to web interface
3. **Metrics storage:** Save latency data to Django database
4. **Mobile viewing:** Optimize web interface for phones

---

## 📝 Technical Notes

### Why This Design:
- **Simplicity:** Easy to understand and modify
- **Performance:** Direct streaming path minimizes latency
- **Compatibility:** Software encoding works everywhere
- **Modularity:** Each component can run independently

### Dependencies:
- **Python 3.x**
- **OpenCV** (`cv2`)
- **FFmpeg** (system installation)
- **MediaMTX** (separate download)
- **Django** (for web interface only)

This system demonstrates professional-grade streaming concepts in a clean, educational package that's perfect for learning and experimentation!