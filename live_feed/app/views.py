from django.shortcuts import render
from django.http import JsonResponse

def live_feed(request):
    """Main view to serve the live feed page"""
    return render(request, 'live_feed.html')

def stream_status(request):
    """Simple endpoint to check if stream is available"""
    return JsonResponse({
        'hls_url': 'http://localhost:8888/zerolatency/index.m3u8',
        'rtsp_url': 'rtsp://localhost:8554/zerolatency',
        'webrtc_url': 'http://localhost:8889/zerolatency'
    })