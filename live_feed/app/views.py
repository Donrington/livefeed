# import socket
# import requests
# from django.shortcuts import render
# from django.http import JsonResponse
# from .config import NetworkConfig

# def live_feed(request):
#     """Main view to serve the live feed page"""
#     # Pass initial stream URLs to template
#     stream_urls = NetworkConfig.get_stream_urls()
#     context = {
#         'initial_urls': stream_urls,
#         'pi_ip': NetworkConfig.PI_VPN_IP,
#         'stream_name': NetworkConfig.STREAM_NAME
#     }
#     return render(request, 'live_feed.html', context)

# def get_local_ip():
#     """Get local IP address - same logic as your publisher/receiver"""
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
#             s.connect(("8.8.8.8", 80))
#             return s.getsockname()[0]
#     except:
#         return "localhost"

# def check_mediamtx_status():
#     """Check if MediaMTX is running on Pi and get stream info"""
#     try:
#         # Try to connect to MediaMTX using configured address
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.settimeout(NetworkConfig.CONNECTION_TIMEOUT)
#         address = NetworkConfig.get_mediamtx_check_address()
#         result = sock.connect_ex(address)
#         sock.close()
#         return result == 0
#     except:
#         return False

# def stream_status(request):
#     """Enhanced endpoint to check stream availability and provide dynamic URLs"""
#     # Get configured stream URLs
#     base_urls = NetworkConfig.get_stream_urls()
#     local_ip = get_local_ip()  # Keep for compatibility
#     mediamtx_running = check_mediamtx_status()
    
#     # Test HLS endpoint availability - COMMENTED OUT (WebRTC preferred)
#     # hls_available = False
#     # try:
#     #     response = requests.head(base_urls['hls_url'], timeout=NetworkConfig.CONNECTION_TIMEOUT)
#     #     hls_available = response.status_code == 200
#     # except:
#     #     hls_available = False
#     hls_available = False  # HLS disabled - using WebRTC + RTSP only
    
#     return JsonResponse({
#         **base_urls,
#         'local_ip': local_ip,
#         'mediamtx_running': mediamtx_running,
#         'hls_available': hls_available,
#         'status': {
#             'mediamtx': 'running' if mediamtx_running else 'not_running',
#             # 'hls': 'available' if hls_available else 'unavailable'  # HLS disabled
#         },
#         'instructions': {
#             'publisher': 'python zero_latency_publisher.py --mediamtx-path "path/to/mediamtx.exe"',
#             'receiver': 'python zero_latency_receiver.py'
#         }
#     })




from django.shortcuts import render
from django.http import JsonResponse
from .config import NetworkConfig
import socket

def live_feed(request):
    """Main view to serve the streaming dashboard"""
    return render(request, 'streaming_dashboard.html')

def stream_status(request):
    """API endpoint to provide stream configuration and status"""
    # Get stream URLs from configuration
    stream_urls = NetworkConfig.get_stream_urls()

    # Check if Pi MediaMTX server is reachable
    pi_reachable = check_pi_connection()

    response_data = {
        'hls_url': stream_urls['hls_url'],
        'rtsp_url': stream_urls['rtsp_url'],
        'webrtc_url': stream_urls['webrtc_url'],
        'pi_ip': NetworkConfig.PI_VPN_IP,
        'windows_ip': NetworkConfig.WINDOWS_VPN_IP,
        'stream_name': NetworkConfig.STREAM_NAME,
        'pi_reachable': pi_reachable,
        'status': 'ready' if pi_reachable else 'pi_unreachable',
        'message': f'Stream URLs configured for Pi IP: {NetworkConfig.PI_VPN_IP}' if pi_reachable else 'Pi MediaMTX server not reachable'
    }

    return JsonResponse(response_data)

def check_pi_connection():
    """Check if Pi MediaMTX server is reachable"""
    try:
        address = NetworkConfig.get_mediamtx_check_address()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(NetworkConfig.CONNECTION_TIMEOUT)
        result = sock.connect_ex(address)
        sock.close()
        return result == 0
    except Exception:
        return False