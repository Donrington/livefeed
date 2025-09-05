import socket
import requests
from django.shortcuts import render
from django.http import JsonResponse

def live_feed(request):
    """Main view to serve the live feed page"""
    return render(request, 'live_feed.html')

def get_local_ip():
    """Get local IP address - same logic as your publisher/receiver"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"

def check_mediamtx_status():
    """Check if MediaMTX is running and get stream info"""
    try:
        # Try to connect to MediaMTX API port (default 9997)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8554))
        sock.close()
        return result == 0
    except:
        return False

def stream_status(request):
    """Enhanced endpoint to check stream availability and provide dynamic URLs"""
    # local_ip = get_local_ip()
    local_ip = "10.9.0.2"
    mediamtx_running = check_mediamtx_status()
    
    # Build URLs using detected IP
    base_urls = {
        'hls_url': f'http://{local_ip}:8888/zerolatency/index.m3u8',
        'rtsp_url': f'rtsp://{local_ip}:8554/zerolatency',
        'webrtc_url': f'http://{local_ip}:8889/zerolatency'
    }
    
    # Test HLS endpoint availability
    hls_available = False
    try:
        response = requests.head(base_urls['hls_url'], timeout=2)
        hls_available = response.status_code == 200
    except:
        hls_available = False
    
    return JsonResponse({
        **base_urls,
        'local_ip': local_ip,
        'mediamtx_running': mediamtx_running,
        'hls_available': hls_available,
        'status': {
            'mediamtx': 'running' if mediamtx_running else 'not_running',
            'hls': 'available' if hls_available else 'unavailable'
        },
        'instructions': {
            'publisher': 'python zero_latency_publisher.py --mediamtx-path "path/to/mediamtx.exe"',
            'receiver': 'python zero_latency_receiver.py'
        }
    })