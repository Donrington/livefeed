# Quick Start: New Dashboard with WebSocket Integration

**🎯 Goal:** Get the new UI running with real-time Pi camera status updates

---

## ⚡ 3-Minute Setup

### 1. **Start Django** (Windows or Pi)
```bash
cd ~/Desktop/livefeed/live_feed
daphne -b 0.0.0.0 -p 9000 live_feed.asgi:application
```

### 2. **Start Publisher** (Raspberry Pi)
```bash
cd ~/Desktop/livefeed
python3 zero_latency_publisher.py \
  --mediamtx-path /home/user/Desktop/mediamtx \
  --ffmpeg-path /usr/bin/ffmpeg
```

### 3. **Open Dashboard** (Browser)
```
http://10.9.0.2:9000  (if Django on Pi)
# OR
http://10.9.0.1:9000  (if Django on Windows)
```

### 4. **Click "Connect" Button**
Watch for:
- ✅ Status changes to "CONNECTED"
- ✅ FPS display shows real numbers (not "30.0" exactly)
- ✅ Console logs: "✅ Connected - waiting for real-time data from Pi..."

---

## 📊 What You'll See

### Connection Successful:
```
Status Badge: 🟢 CONNECTED
FPS Display: 29.8 fps (updates every second)
Health: 100%
Connection: 100%
Quality: 95%
```

### Console Output (Browser):
```javascript
🔌 Connecting to camera system...
✅ Connected to camera system
✅ Connected - waiting for real-time data from Pi...
📶 Pi camera status: true | FPS: 30.1
```

### Console Output (Pi Publisher):
```
[12:34:56] MainThread INFO: Stream will be available at: rtsp://10.9.0.2:8554/zerolatency
[12:34:56] MainThread INFO: MediaMTX started successfully
[12:34:57] MainThread INFO: Starting publishing frames to client
[12:34:57] Thread-1 INFO: started websocket thread
[12:34:57] Thread-1 INFO: connecting to ws://10.9.0.1:9000/ws/camera/
[12:34:58] Thread-1 INFO: WebSocket connected
```

---

## 🔍 Debugging

### Problem: "NOT CONNECTED" stays red

**Check 1:** Is Django running?
```bash
netstat -tuln | grep 9000
# Should show: 0.0.0.0:9000 LISTEN
```

**Check 2:** Is Pi Publisher connected to Django?
```bash
# Check Pi publisher logs for:
[Thread-1] INFO: WebSocket connected  ✅ Good!
[Thread-1] ERROR: Connection error    ❌ Bad!
```

**Check 3:** Is config pointing to correct IP?
```python
# In live_feed/app/config.py:
WINDOWS_VPN_IP = "10.9.0.1"  # Should match Django location
PI_VPN_IP = "10.9.0.2"
WEBSOCKET_PORT = 9000
```

---

### Problem: FPS shows "0" or doesn't update

**Reason:** Publisher not sending messages to Django

**Fix 1:** Check Publisher WebSocket URI
```python
# In zero_latency_publisher.py line ~60:
uri = f"ws://{NetworkConfig.WINDOWS_VPN_IP}:{NetworkConfig.WEBSOCKET_PORT}/ws/camera/"
# Should connect to WHERE DJANGO IS RUNNING
```

**Fix 2:** Check browser console for messages
```javascript
// Open DevTools → Console
// Should see messages arriving (even if commented out)
```

---

### Problem: Metrics show fake data (not Real FPS)

**Check:** Make sure you're using the NEW file!
```bash
# You should be viewing:
live_feed/templates/streaming_dashboard_backup.html

# NOT the old one:
live_feed/templates/streaming_dashboard.html
```

**Verify:** Check for this in the script section (line ~1319):
```javascript
// === REMOVED: startMetricsSimulation() ===
console.log('✅ Connected - waiting for real-time data from Pi...');
```

If you see `startMetricsSimulation()` being called, you're on the OLD file!

---

## 🧪 Test Scenarios

### Test 1: Real-Time Updates
1. Connect dashboard
2. Watch FPS display
3. It should show: **29.8, 30.1, 29.9** (varying slightly)
4. NOT: **30.0** (fixed - that's fake data!)

### Test 2: Camera Disconnect
1. While connected, unplug camera on Pi
2. Watch health indicator drop to 50%
3. Console shows: "⚠️ Camera feed interrupted!"

### Test 3: Multiple Dashboards
1. Open dashboard in 2 browser windows
2. Both should receive same FPS updates
3. Both should show same connection status

---

## 📝 Quick Reference

### Files Modified:
- ✅ `live_feed/templates/streaming_dashboard_backup.html` (NEW UI with WebSocket)

### Files Created:
- ✅ `docs/UI_Migration_Summary.md` (Full migration guide)
- ✅ `docs/Message_Flow_Explained.md` (Technical deep-dive)
- ✅ `docs/QUICK_START_NEW_UI.md` (This file!)

### Configuration Required:
```python
# live_feed/app/config.py
WINDOWS_VPN_IP = "10.9.0.1"  # Django location
PI_VPN_IP = "10.9.0.2"       # Pi location
WEBSOCKET_PORT = 9000        # Match Daphne port
```

---

## 🎯 Success Criteria

### ✅ You're Done When:
1. Dashboard shows "CONNECTED" status
2. FPS counter displays real numbers (not fixed 30.0)
3. Browser console shows no errors
4. Pi publisher logs show "WebSocket connected"

### ❌ Not Working If:
1. Status stays "NOT CONNECTED"
2. FPS shows "0" or doesn't update
3. Console shows: "Connection error: [Errno 111]"
4. Metrics show the EXACT same fake values

---

## 🚀 Next Steps After Success

1. **Test video streaming** (connect cameras)
2. **Add real metrics** to Pi publisher (CPU, memory)
3. **Customize UI** for your needs
4. **Deploy to production** with proper config

---

## 💡 Pro Tips

### Tip 1: Use Browser DevTools
```javascript
// Open Console (F12) and run:
console.log('WebSocket state:', cameraWebSocket.readyState);
// 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
```

### Tip 2: Monitor Message Rate
```javascript
// In console, watch messages arrive:
cameraWebSocket.onmessage = function(event) {
    console.log('📨', event.data);
};
```

### Tip 3: Check Network Tab
- Open DevTools → Network → WS (WebSocket)
- See all messages in/out
- Verify messages arriving at ~30/second

---

## 📞 Need Help?

1. **Check logs:** Browser console + Pi terminal
2. **Review docs:** `docs/Message_Flow_Explained.md`
3. **Compare files:** Old vs new dashboard
4. **Verify config:** IPs, ports, paths

---

**Good luck!** 🎉 You're now running a modern surveillance dashboard with real-time Pi camera integration!

*Last Updated: October 6, 2025*
*Status: Ready for Testing*
