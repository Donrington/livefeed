# streaming/config.py
from django.conf import settings

class StreamingConfig:
#    Centralized configuration for streaming components
    
    def __init__(self):
        self.config = getattr(settings, 'STREAMING_CONFIG', {})
    
    @property
    def django_server_url(self):
        return self.config.get('DJANGO_SERVER_URL', 'http://localhost:8000')
    
    @property
    def camera_index(self):
        return self.config.get('CAMERA_INDEX', 0)
    
    @property
    def video_width(self):
        return self.config.get('VIDEO_WIDTH', 1280)
    
    @property
    def video_height(self):
        return self.config.get('VIDEO_HEIGHT', 720)
    
    @property
    def video_fps(self):
        return self.config.get('VIDEO_FPS', 30)
    
    @property
    def video_bitrate(self):
        return self.config.get('VIDEO_BITRATE', '1200k')
    
    @property
    def gop_size(self):
        return self.config.get('GOP_SIZE', 15)
    
    @property
    def ffmpeg_preset(self):
        return self.config.get('FFMPEG_PRESET', 'ultrafast')
    
    @property
    def ffmpeg_tune(self):
        return self.config.get('FFMPEG_TUNE', 'zerolatency')
    
    def get_rtsp_url(self):
        base_url = self.config.get('MEDIAMTX_RTSP_URL', 'rtsp://localhost:8554')
        stream_name = self.config.get('STREAM_NAME', 'mystream')
        return f"{base_url}/{stream_name}"
    
    def get_hls_url(self):
        base_url = self.config.get('MEDIAMTX_HLS_URL', 'http://localhost:8888')
        stream_name = self.config.get('STREAM_NAME', 'mystream')
        return f"{base_url}/{stream_name}/index.m3u8"

