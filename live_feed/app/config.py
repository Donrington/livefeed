# Network Configuration for Live Feed System
"""
Centralized configuration for IP addresses, ports, and stream settings.
This makes it easy to update network settings without hunting through multiple files.
"""

# VPN Network Configuration
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
    
    # Connection Settings
    CONNECTION_TIMEOUT = 2  # seconds
    
    @classmethod
    def get_stream_urls(cls):
        """Generate all stream URLs based on current configuration"""
        return {
            # 'hls_url': f'http://{cls.PI_VPN_IP}:{cls.HLS_PORT}/{cls.STREAM_NAME}/index.m3u8',  # HLS disabled
            'hls_url': None,  # HLS disabled - WebRTC preferred
            'rtsp_url': f'rtsp://{cls.PI_VPN_IP}:{cls.RTSP_PORT}/{cls.STREAM_NAME}',
            'webrtc_url': f'http://{cls.PI_VPN_IP}:{cls.WEBRTC_PORT}/{cls.STREAM_NAME}/whep'
        }
    
    @classmethod
    def get_mediamtx_check_address(cls):
        """Get address for checking if MediaMTX is running"""
        return (cls.PI_VPN_IP, cls.RTSP_PORT)

# Development/Fallback Configuration
class DevConfig:
    # Fallback to localhost for development
    LOCALHOST = "localhost"
    
    @classmethod
    def get_stream_urls(cls):
        """Generate localhost URLs for development/testing"""
        return {
            # 'hls_url': f'http://{cls.LOCALHOST}:{NetworkConfig.HLS_PORT}/{NetworkConfig.STREAM_NAME}/index.m3u8',  # HLS disabled
            'hls_url': None,  # HLS disabled - WebRTC preferred
            'rtsp_url': f'rtsp://{cls.LOCALHOST}:{NetworkConfig.RTSP_PORT}/{NetworkConfig.STREAM_NAME}',
            'webrtc_url': f'http://{cls.LOCALHOST}:{NetworkConfig.WEBRTC_PORT}/{NetworkConfig.STREAM_NAME}/whep'
        }

# Default to production network config
DEFAULT_CONFIG = NetworkConfig