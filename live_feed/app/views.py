


from django.shortcuts import render
from django.http import JsonResponse
from .config import NetworkConfig
import socket

def live_feed(request):
    """Main view to serve the streaming dashboard"""
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only content partial for AJAX with metadata
        context = {
            'page_css': 'css/dashboard.css',
            'page_js': 'js/dashboard.js',
            'page_name': 'dashboard'
        }
        return render(request, 'partials/dashboard_content.html', context)
    # Full page for initial load
    return render(request, 'streaming_dashboard.html')

def settings(request):
    """Main view to serve the settings dashboard"""
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only content partial for AJAX with metadata
        context = {
            'page_css': 'css/settings.css',
            'page_js': 'js/settings.js',
            'page_name': 'settings'
        }
        return render(request, 'partials/settings_content.html', context)
    # Full page for initial load
    return render(request, 'settings.html')

def analytics(request):
    """Sub view to serve the analytics page"""
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only content partial for AJAX with metadata
        context = {
            'page_css': 'css/analytics.css',
            'page_js': 'js/analytics.js',
            'page_name': 'analytics',
            'external_js': 'https://cdn.jsdelivr.net/npm/chart.js'  # Chart.js CDN
        }
        return render(request, 'partials/analytics_content.html', context)
    # Full page for initial load
    return render(request, 'analytics.html')

def recordings(request):
    """View to serve the Recordings page"""
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only content partial for AJAX with metadata
        context = {
            'page_css': 'css/live_stream.css',
            'page_js': None,  # Recordings has inline JS
            'page_name': 'recordings'
        }
        return render(request, 'partials/recordings_content.html', context)
    # Full page for initial load
    return render(request, 'recordings.html')

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