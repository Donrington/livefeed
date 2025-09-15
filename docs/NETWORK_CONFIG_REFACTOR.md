# Network Configuration Refactor

## Overview
Refactored the live feed system to eliminate hardcoded localhost URLs and centralize network configuration for better maintainability and clarity.

## Changes Made

### 1. Created Centralized Configuration (`app/config.py`)

```python
class NetworkConfig:
    # VPN IP Addresses
    WINDOWS_VPN_IP = "10.9.0.1"  # Windows machine VPN IP
    PI_VPN_IP = "10.9.0.2"       # Raspberry Pi VPN IP
    
    # MediaMTX Server Ports (running on Pi)
    RTSP_PORT = 8554
    HLS_PORT = 8888
    WEBRTC_PORT = 8889
    
    # Stream Configuration
    STREAM_NAME = "zerolatency"
    CONNECTION_TIMEOUT = 2
```

**Benefits:**
- Single source of truth for all network settings
- Easy to update IP addresses and ports
- Clear documentation of the network topology
- Consistent timeout values across the application

### 2. Updated Django Views (`app/views.py`)

**Before:**
```python
pi_ip = "10.9.0.2"  # Hardcoded
base_urls = {
    'hls_url': f'http://{pi_ip}:8888/zerolatency/index.m3u8',  # Hardcoded ports
    'rtsp_url': f'rtsp://{pi_ip}:8554/zerolatency',
    'webrtc_url': f'http://{pi_ip}:8889/zerolatency/whep'
}
```

**After:**
```python
from .config import NetworkConfig

base_urls = NetworkConfig.get_stream_urls()  # Clean method call
```

**Benefits:**
- No more scattered hardcoded IP addresses
- Consistent URL generation
- Easy to add new stream types
- Better error handling with centralized timeout

### 3. Updated HTML Template (`templates/live_feed.html`)

**Before:**
```html
<code class="url-code" id="hlsUrl">http://localhost:8888/zerolatency/index.m3u8</code>
```

**After:**
```html
<code class="url-code" id="hlsUrl">{{ initial_urls.hls_url }}</code>
```

**Benefits:**
- No more confusing localhost placeholders
- Shows actual Pi IP addresses immediately
- Users can copy-paste URLs without confusion
- Consistent with backend configuration

### 4. Enhanced JavaScript Configuration

**Before:**
```javascript
let streamUrls = {
    hls: 'http://localhost:8888/zerolatency/index.m3u8',  // Placeholder
    rtsp: 'rtsp://localhost:8554/zerolatency',
    webrtc: 'http://localhost:8889/zerolatency'
};
```

**After:**
```javascript
// Network Configuration (from Django backend)
const NETWORK_CONFIG = {
    PI_IP: '{{ pi_ip }}',
    STREAM_NAME: '{{ stream_name }}',
};

// Stream URLs - initialized from server configuration
let streamUrls = {
    hls: '{{ initial_urls.hls_url }}',     // Real Pi IP from start
    rtsp: '{{ initial_urls.rtsp_url }}',
    webrtc: '{{ initial_urls.webrtc_url }}'
};
```

**Benefits:**
- JavaScript has access to network configuration
- No URL mismatches between frontend and backend
- Clear documentation of where values come from

## Problem Solved

### Before Refactor:
- Users saw `localhost:8888` in UI but actual stream was `10.9.0.2:8888`
- Hardcoded IPs scattered across multiple files
- Confusing for users trying to understand the system
- Difficult to update network settings

### After Refactor:
- Users see actual Pi IP (`10.9.0.2:8888`) immediately
- All network settings in one configuration file
- Clear understanding of VPN topology
- Easy to update for different network configurations

## Network Topology Documentation

```
Windows Machine (10.9.0.1)          Raspberry Pi (10.9.0.2)
├── Django Web App (Port 8080)       ├── MediaMTX Server
├── Zero Latency Receiver             │   ├── RTSP: 8554
└── VPN Client                        │   ├── HLS: 8888
                                      │   └── WebRTC: 8889
                                      ├── Zero Latency Publisher
                                      └── VPN Server
```

## Usage

### To Change Network Configuration:
1. Edit `app/config.py`
2. Update IP addresses or ports as needed
3. Restart Django server
4. All URLs automatically update across the system

### To Add New Stream Type:
1. Add port to `NetworkConfig` class
2. Update `get_stream_urls()` method
3. URLs will be available in templates and API

## Files Modified:
- `app/config.py` (new file)
- `app/views.py`
- `templates/live_feed.html`

## Testing Verified:
- ✅ Django server starts without errors
- ✅ API endpoint returns correct Pi IP URLs
- ✅ HTML template renders Pi IPs instead of localhost
- ✅ All URLs show `10.9.0.2` as expected

## Future Improvements:
- Could add environment variable support for different deployments
- Could add network connectivity testing methods
- Could add automatic IP discovery for dynamic networks