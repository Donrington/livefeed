# 🎥 Live Surveillance System with Latency Monitoring

## What We Built - The Big Picture

Imagine you want to watch your webcam live on any device in your house, while also measuring how much delay (latency) there is between what's happening in real life and what you see on screen.

We built a complete system that:
1. **Captures video** from your webcam 📹
2. **Streams it live** to any web browser 🌐
3. **Measures the delay** between capture and viewing ⏱️
4. **Shows you a dashboard** with all the statistics 📊

Think of it like a mini YouTube Live, but running on your own computer!

---

## 🏗️ The Three Main Parts (Components)

### 1. 🏢 The Server (Django Web App)
**What it does:** Like a central command center
- Creates a website you can visit to watch the stream
- Stores information about video quality and delays
- Shows you statistics and graphs

**Files involved:**
- `app/models.py` - Stores data in a database
- `app/views.py` - Creates web pages and handles requests
- `templates/` - The actual web page you see

### 2. 📤 The Publisher (Video Sender)
**What it does:** Takes video from your webcam and sends it out
- Grabs frames from your camera
- Adds blue timestamps to track timing
- Converts video to a format that can be streamed
- Sends it to MediaMTX (the streaming server)

**File:** `streaming/publisher.py`

### 3. 📥 The Receiver (Video Watcher)
**What it does:** Watches the stream and measures delays
- Receives the streamed video
- Adds red timestamps showing when it received the video
- Calculates how long the delay was
- Shows you the video with both timestamps

**File:** `streaming/receiver.py`

---

## 🚀 How It All Works Together

```
[Your Webcam] 
    ↓ (captures video)
[Publisher] 
    ↓ (adds blue timestamp, sends via RTSP)
[MediaMTX Server] 
    ↓ (converts to web-friendly format)
[Your Web Browser] + [Receiver]
    ↓ (both watch the stream)
[Django Database] (stores timing data)
```

### The Journey of One Video Frame:

1. **📹 Camera captures** a frame at 01:20:30.100
2. **🔵 Publisher adds blue timestamp** "PUB: 01:20:30.100" 
3. **📡 Publisher sends** to MediaMTX server
4. **🔄 MediaMTX converts** to web format (HLS)
5. **🌐 Browser shows** the video on your dashboard
6. **🔴 Receiver adds red timestamp** "REC: 01:20:30.300"
7. **⏱️ System calculates** delay: 300 - 100 = 200ms delay

---

## 📁 File Structure Explanation

```
live_feed/                          # Main project folder
├── manage.py                       # Django's control panel
├── requirements.txt                # List of needed software
├── live_feed/                      # Project settings
│   ├── settings.py                 # Configuration file
│   └── urls.py                     # Website routes
├── app/                            # Main Django application
│   ├── models.py                   # Database structure
│   ├── views.py                    # Web page logic
│   ├── urls.py                     # Page routes
│   └── migrations/                 # Database setup files
├── templates/                      # Web page designs
├── static/                         # CSS, images, etc.
└── streaming/                      # Video streaming code
    ├── config.py                   # Settings for streaming
    ├── base.py                     # Common functions
    ├── publisher.py                # Sends video
    └── receiver.py                 # Receives video
```

---

## 📝 Code Breakdown - What Each File Does

### 🔧 `live_feed/settings.py` (Configuration)
```python
STREAMING_CONFIG = {
    'CAMERA_INDEX': 0,              # Which camera to use (0 = first camera)
    'VIDEO_WIDTH': 1280,            # Video width in pixels
    'VIDEO_HEIGHT': 720,            # Video height in pixels
    'VIDEO_FPS': 30,                # Frames per second
    'GOP_SIZE': 15,                 # How often to send full frames
}
```
**Translation:** "Use the first camera, record in HD quality (1280x720), capture 30 frames per second, and send a complete frame every 15 frames for efficiency."

### 🗃️ `app/models.py` (Database Structure)
```python
class StreamMetrics(models.Model):
    timestamp = models.DateTimeField()    # When this was recorded
    publisher_fps = models.FloatField()   # How fast publisher is sending
    receiver_fps = models.FloatField()    # How fast receiver is getting
    latency_ms = models.FloatField()      # Delay in milliseconds
    frame_number = models.IntegerField()  # Which frame this is
```
**Translation:** "Create a database table to store information about each measurement: when it happened, how fast each part is working, what the delay was, and which video frame we're talking about."

### 🎬 `streaming/publisher.py` (Video Sender)

#### Camera Setup:
```python
def setup_camera(self):
    self.cap = cv2.VideoCapture(0)  # Connect to first camera
    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Use tiny buffer for speed
```
**Translation:** "Connect to the camera and tell it to not save up frames - send them immediately for lowest delay."

#### Adding Timestamps:
```python
def add_timestamp_overlay(self, frame):
    current_time = datetime.now()
    timestamp_text = f"PUB: {current_time.strftime('%H:%M:%S.%f')[:-3]}"
    cv2.putText(frame, timestamp_text, (10, 30), font, font_scale, blue_color, thickness)
```
**Translation:** "Get the exact current time, format it nicely, and write it in blue text on the top-left of the video frame so we can see when this frame was sent."

#### FFmpeg Streaming:
```python
ffmpeg_cmd = [
    'ffmpeg', '-y',           # Use FFmpeg video converter
    '-f', 'rawvideo',         # Input is raw video data
    '-c:v', 'libx264',        # Convert to H.264 format
    '-preset', 'ultrafast',   # Prioritize speed over file size
    '-tune', 'zerolatency',   # Optimize for lowest delay
    '-f', 'rtsp',            # Output as RTSP stream
    rtsp_url                 # Send to this address
]
```
**Translation:** "Take the raw video from the camera, convert it to H.264 format (which browsers understand), do it as fast as possible with lowest delay, and send it to the MediaMTX server."

### 📺 `streaming/receiver.py` (Video Watcher)

#### Stream Connection:
```python
def setup_stream(self):
    hls_url = "http://localhost:8888/mystream/index.m3u8"
    self.cap = cv2.VideoCapture(hls_url)
```
**Translation:** "Connect to the web stream that MediaMTX is providing and get ready to watch it."

#### Latency Calculation:
```python
def calculate_latency(self):
    latest_metric = StreamMetrics.objects.filter(publisher_fps__gt=0).order_by('-id').first()
    current_time = time.time() * 1000
    db_time = latest_metric.timestamp.timestamp() * 1000
    latency = current_time - db_time
```
**Translation:** "Look in the database for the most recent timing from the publisher, compare it with the current time, and calculate how much delay there was."

### 🌐 `app/views.py` (Web Interface)
```python
def live_feed(request):
    return render(request, 'live_feed.html')

def get_metrics(request):
    latest_metrics = StreamMetrics.objects.first()
    return JsonResponse({
        'publisher_fps': latest_metrics.publisher_fps,
        'receiver_fps': latest_metrics.receiver_fps,
        'latency_ms': latest_metrics.latency_ms,
    })
```
**Translation:** "When someone visits the website, show them the live video page. When they ask for statistics, look up the latest measurements in the database and send them back."

---

## ⚙️ MediaMTX Configuration Explained

MediaMTX is a separate program that acts like a video traffic controller. Here's what our settings mean:

```yaml
hls: yes                         # Enable web browser streaming
hlsAddress: :8888               # Run on port 8888
hlsVariant: lowLatency          # Use fastest streaming method
hlsSegmentCount: 7              # Keep 7 video chunks (required minimum)
hlsSegmentDuration: 200ms       # Each chunk is 0.2 seconds long
hlsPartDuration: 50ms           # Sub-chunks are 0.05 seconds long
hlsAlwaysRemux: yes            # Always keep converting video
hlsAllowOrigin: '*'            # Let any website access this
```

**What this means:** "Accept video from the publisher, chop it into tiny 0.2-second pieces for web browsers to download quickly, keep 7 pieces available at once (for smooth playback), and let any web page access this stream."

---

## 🔄 The Complete Data Flow

### Step 1: Video Capture
```
Camera → Publisher reads frame → Adds blue timestamp → Current time: 10:30:45.123
```

### Step 2: Streaming
```
Publisher → FFmpeg → MediaMTX → Converts to web format
```

### Step 3: Database Recording
```
Publisher → Saves to database: "Frame 150, sent at 10:30:45.123, 30 FPS"
```

### Step 4: Web Viewing
```
Browser → Requests stream from MediaMTX → Shows video with blue timestamp
```

### Step 5: Latency Measurement
```
Receiver → Watches same stream → Adds red timestamp → Current time: 10:30:45.323
Receiver → Calculates: 323 - 123 = 200ms delay
Receiver → Updates database: "Received at 10:30:45.323, 200ms delay"
```

### Step 6: Dashboard Display
```
Web page → Asks Django for latest stats → Shows: "Latency: 200ms, FPS: 30"
```

---

## 🎯 Why We Measure Latency

**Latency** = How long it takes from when something happens in real life to when you see it on screen.

### Good vs Bad Latency:
- **🟢 Under 100ms:** Excellent (like video calls)
- **🟡 100-500ms:** Good (like live TV)
- **🟠 500ms-2s:** Acceptable (like YouTube Live)
- **🔴 Over 2s:** Poor (like old satellite TV)

### Our System's Performance:
- **HLS Streaming:** Usually 2-3 seconds (which is actually very good!)
- **Publisher to Database:** Usually under 50ms
- **Network delays:** Usually 100-300ms

---

## 🚀 Setup Instructions (Step by Step)

### Prerequisites (Software You Need):
1. **Python 3.8+** (programming language)
2. **FFmpeg** (video converter)
3. **MediaMTX** (streaming server)
4. **A webcam** (obviously!)

### Step 1: Install Python Dependencies
```bash
cd live_feed
pip install -r requirements.txt
```
**Translation:** "Install all the Python libraries our code needs."

### Step 2: Setup Database
```bash
python manage.py makemigrations app
python manage.py migrate
```
**Translation:** "Create the database tables where we'll store our measurements."

### Step 3: Configure Settings
Edit `live_feed/settings.py` and adjust:
```python
STREAMING_CONFIG = {
    'CAMERA_INDEX': 0,     # Change if you have multiple cameras
    'VIDEO_WIDTH': 1280,   # Lower if your computer is slow
    'VIDEO_HEIGHT': 720,   # Lower if your computer is slow
}
```

---

## 🏃‍♂️ How to Run Everything

### The Order Matters! (Like starting a car)

#### 1. Start MediaMTX (The Traffic Controller)
```bash
# In MediaMTX folder
mediamtx.exe -config mediamtx.yml
```
**Wait for:** "listener opened on :8554"

#### 2. Start Django (The Website)
```bash
# In live_feed folder
python manage.py runserver 8000
```
**Wait for:** "Starting development server"

#### 3. Start Publisher (The Video Sender)
```bash
# In live_feed folder
python streaming/publisher.py
```
**Wait for:** "Publisher started successfully"

#### 4. Start Receiver (The Delay Measurer)
```bash
# In live_feed folder
python streaming/receiver.py
```

### What You'll See:
- **Publisher window:** Your camera with blue timestamps
- **Receiver window:** Same video with red timestamps
- **Web browser:** Visit `http://localhost:8000` for the dashboard

---

## 🐛 Common Problems and Solutions

### "FFmpeg not found"
**Problem:** Computer can't find FFmpeg
**Solution:** Download FFmpeg and add to Windows PATH, or put `ffmpeg.exe` in your project folder

### "Could not open camera"
**Problem:** Camera is being used by another program
**Solution:** Close other camera apps (Zoom, Skype, etc.)

### "Stream not available"
**Problem:** Started components in wrong order
**Solution:** Start MediaMTX first, then Publisher, then Receiver

### High latency (over 3 seconds)
**Problem:** Settings too conservative
**Solution:** In MediaMTX config, try smaller segment durations:
```yaml
hlsSegmentDuration: 100ms
hlsPartDuration: 25ms
```

---

## 📊 Understanding the Dashboard

### What the Numbers Mean:

#### Publisher FPS
**Example:** 29.8 FPS
**Meaning:** "The publisher is capturing and sending 29.8 frames per second"
**Good:** Close to your target (usually 30)
**Bad:** Much lower than target (indicates camera or CPU problems)

#### Receiver FPS  
**Example:** 29.5 FPS
**Meaning:** "The receiver is getting 29.5 frames per second"
**Good:** Close to publisher FPS
**Bad:** Much lower (indicates network or processing problems)

#### Latency
**Example:** 250ms
**Meaning:** "There's a 250 millisecond delay from capture to viewing"
**Excellent:** Under 100ms
**Good:** 100-500ms
**Acceptable:** 500ms-2s
**Poor:** Over 2s

### Color Coding:
- **🟢 Green:** Everything working well
- **🟡 Yellow:** Minor issues, still usable
- **🔴 Red:** Problems that need attention

---

## 🔧 Advanced Optimizations

### For Lower Latency:
1. **Reduce video quality:** 640x480 instead of 1280x720
2. **Increase bitrate:** More bandwidth = less compression delay
3. **Use hardware encoding:** If your graphics card supports it
4. **Shorter segments:** 100ms instead of 200ms

### For Better Quality:
1. **Increase bitrate:** 2000k instead of 1200k
2. **Use slower preset:** "fast" instead of "ultrafast"
3. **Higher resolution:** 1920x1080 instead of 1280x720

### For Stability:
1. **Longer segments:** 500ms instead of 200ms
2. **More segments:** 10 instead of 7
3. **Bigger buffers:** Increase buffer sizes

---

## 🎓 What You Learned

By building this system, you've learned about:

1. **Video Streaming:** How live video gets from cameras to screens
2. **Latency Measurement:** How to measure and optimize delays
3. **Web Development:** Building dashboards with Django
4. **Database Design:** Storing and retrieving time-series data
5. **System Integration:** Making multiple programs work together
6. **Performance Optimization:** Balancing quality, speed, and stability

### Technologies Used:
- **Python:** Programming language
- **Django:** Web framework  
- **OpenCV:** Computer vision library
- **FFmpeg:** Video processing
- **MediaMTX:** Streaming server
- **HLS:** Web streaming protocol
- **HTML/JavaScript:** Web interface

---

## 🚀 Next Steps

### Possible Improvements:
1. **Add authentication:** Require login to view streams
2. **Multiple cameras:** Support several cameras at once
3. **Recording:** Save video files automatically
4. **Motion detection:** Alert when something moves
5. **Mobile app:** View streams on your phone
6. **Cloud deployment:** Access from anywhere

### Learning Path:
1. **Understand the basics** (you're here!)
2. **Experiment with settings** 
3. **Add new features**
4. **Learn about WebRTC** for even lower latency
5. **Study video codecs** for better quality
6. **Explore AI integration** for smart alerts

---

## 📞 Support

If something doesn't work:
1. **Check the startup order** (MediaMTX → Django → Publisher → Receiver)
2. **Verify all software is installed** (Python, FFmpeg, etc.)
3. **Look at the error messages** (they usually tell you what's wrong)
4. **Test each component separately**
5. **Check your camera permissions** (Windows may block camera access)

Remember: Every expert was once a beginner! This system touches on many complex topics, so don't worry if it takes time to understand everything.

---

## 🎉 Congratulations!

You've built a complete, professional-grade surveillance system with latency monitoring. This is the same type of technology used by:
- Live streaming platforms (Twitch, YouTube Live)
- Video conferencing (Zoom, Teams)
- Security companies (professional CCTV systems)
- Broadcasting networks (live TV)

You now understand the fundamentals of modern video streaming technology!