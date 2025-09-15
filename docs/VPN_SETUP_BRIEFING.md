# VPN Setup Briefing: Windows-Pi Live Feed Connection

## Overview
Successfully configured a live video streaming system where:
- **Windows (10.9.0.1)**: VPN Server + Django Web Interface
- **Raspberry Pi (10.9.0.2)**: VPN Client + Video Publisher

## Architecture
```
[Pi Camera] → [MediaMTX on Pi] → [VPN Tunnel] → [Django Web App on Windows] → [Browser]
     📷             🎥              🔗              💻                    🌐
```

## Key Changes Made

### 1. MediaMTX Configuration (Pi)
**Problem**: MediaMTX was binding to localhost only
```yaml
# Before (localhost only)
webrtcAddress: :8889
rtspAddress: :8554  
hlsAddress: :8888

# After (all interfaces)
webrtcAddress: 0.0.0.0:8889
rtspAddress: 0.0.0.0:8554
hlsAddress: 0.0.0.0:8888
```

### 2. Publisher Configuration (Pi)
**File**: `zero_latency_publisher.py`
- Changed RTSP URL to use VPN IP explicitly
- Stream now publishes to: `rtsp://10.9.0.2:8554/zerolatency`

### 3. Django App Configuration (Windows)
**File**: `live_feed/app/views.py`
- Updated stream URLs to point to Pi's VPN IP
- HLS: `http://10.9.0.2:8888/zerolatency/index.m3u8`
- RTSP: `rtsp://10.9.0.2:8554/zerolatency`
- WebRTC: `http://10.9.0.2:8889/zerolatency`

### 4. Firewall Rules (Pi)
```bash
# Allow VPN traffic
sudo ufw allow in on tun0
sudo ufw allow out on tun0

# Allow MediaMTX ports from Windows
sudo ufw allow from 10.9.0.1 to any port 8554  # RTSP
sudo ufw allow from 10.9.0.1 to any port 8888  # HLS
sudo ufw allow from 10.9.0.1 to any port 8889  # WebRTC

# Allow SSH over VPN
sudo ufw allow from 10.9.0.1 to any port 22
```

## Network Flow
1. **Pi**: Camera → MediaMTX → Streams on all interfaces (0.0.0.0)
2. **VPN**: Tunnel carries stream data from Pi (10.9.0.2) to Windows (10.9.0.1)
3. **Windows**: Django serves web interface pointing to Pi's VPN streams
4. **Browser**: Connects to Windows Django, receives Pi streams via VPN

## Stream Access Points
- **HLS Stream**: `http://10.9.0.2:8888/zerolatency/index.m3u8`
- **RTSP Stream**: `rtsp://10.9.0.2:8554/zerolatency`
- **WebRTC Stream**: `http://10.9.0.2:8889/zerolatency`
- **Web Interface**: `http://10.9.0.1:8001` (Django on Windows)

## Key Learnings
1. **Binding Importance**: Services must bind to `0.0.0.0` not `localhost` for VPN access
2. **Firewall Configuration**: VPN interface (`tun0`) needs explicit allow rules
3. **Cross-Network Streaming**: Publisher and consumer can be on different network segments
4. **Port Management**: Each protocol (RTSP/HLS/WebRTC) needs individual firewall rules

## Test Commands
```bash
# From Windows - Test Pi connectivity
ping 10.9.0.2
telnet 10.9.0.2 8554  # RTSP port
curl http://10.9.0.2:8888/zerolatency/index.m3u8  # HLS

# From Pi - Test Windows connectivity  
ping 10.9.0.1
ssh user@10.9.0.1
```

## Status: ✅ WORKING
- VPN tunnel established
- Pi publishing video streams
- Windows serving web interface
- Cross-network video streaming functional