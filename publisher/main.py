# publisher/main.py (UPDATED)
import sys
import os

# Add the parent directory to Python path so we can import 'shared'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


# Now we can import from shared
from shared.base import HTTPMetricsReporter, NullMetricsReporter, StreamComponent


import cv2
import numpy as np
import subprocess
import signal
import atexit
import time
from datetime import datetime

class RTSPPublisher(StreamComponent):
    """Standalone RTSP Publisher - No Django dependency"""
    
    def __init__(self, config=None, metrics_reporter=None):
        super().__init__("Publisher")
        self.config = config or self.default_config()
        self.metrics_reporter = metrics_reporter or NullMetricsReporter()
        self.cap = None
        self.ffmpeg_process = None
        self.frame_number = 0
        
        # Register cleanup handlers
        atexit.register(self.emergency_cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def default_config(self):
        """Default configuration if no config provided"""
        class DefaultConfig:
            camera_index = 0
            video_width = 1280
            video_height = 720
            video_fps = 30
            video_bitrate = '1200k'
            gop_size = 15
            ffmpeg_preset = 'ultrafast'
            ffmpeg_tune = 'zerolatency'
            rtsp_url = 'rtsp://localhost:8554/mystream'
            metrics_api_url = 'http://localhost:8000/api/metrics/publisher/'
        return DefaultConfig()
        
    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        self.log("Received termination signal")
        self.stop()
        sys.exit(0)
        
    def emergency_cleanup(self):
        """Emergency cleanup on exit"""
        self.log("Emergency cleanup triggered")
        self.stop()
        
    def setup_camera(self):
        """Initialize camera capture"""
        self.log("Setting up camera...")
        
        # Release any existing camera
        if self.cap is not None:
            self.cap.release()
            time.sleep(1)
        
        # Open camera with retries
        for attempt in range(3):
            try:
                self.cap = cv2.VideoCapture(self.config.camera_index)
                if self.cap.isOpened():
                    break
                self.cap.release()
                time.sleep(2)
            except Exception as e:
                self.log(f"Camera attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        
        if not self.cap.isOpened():
            raise Exception(f"Could not open camera {self.config.camera_index}")
        
        # Configure camera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.video_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.video_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.config.video_fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Test frame reading
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Camera opened but cannot read frames")
            
        self.log(f"Camera ready: {self.config.video_width}x{self.config.video_height}@{self.config.video_fps}fps")
        
    def setup_ffmpeg_rtsp(self):
        """Setup FFmpeg RTSP streaming"""
        self.log(f"Setting up FFmpeg stream to {self.config.rtsp_url}")
        
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{self.config.video_width}x{self.config.video_height}',
            '-r', str(self.config.video_fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', self.config.ffmpeg_preset,
            '-tune', self.config.ffmpeg_tune,
            '-g', str(self.config.gop_size),
            '-keyint_min', str(self.config.gop_size),
            '-sc_threshold', '0',
            '-b:v', self.config.video_bitrate,
            '-maxrate', self.config.video_bitrate,
            '-bufsize', f'{int(self.config.video_bitrate[:-1]) * 2}k',
            '-f', 'rtsp',
            self.config.rtsp_url
        ]
        
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
    def add_timestamp_overlay(self, frame):
        """Add blue timestamp overlay"""
        current_time = datetime.now()
        timestamp_ms = int(current_time.timestamp() * 1000)
        
        # Create overlay texts
        timestamp_text = f"PUB: {current_time.strftime('%H:%M:%S.%f')[:-3]}"
        fps_text = f"FPS: {self.current_fps:.1f}"
        frame_text = f"Frame: {self.frame_number}"
        
        # Blue color overlay
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        blue_color = (255, 0, 0)  # BGR
        
        cv2.putText(frame, timestamp_text, (10, 30), font, font_scale, blue_color, thickness)
        cv2.putText(frame, fps_text, (10, 60), font, font_scale, blue_color, thickness)
        cv2.putText(frame, frame_text, (10, 90), font, font_scale, blue_color, thickness)
        
        return frame, timestamp_ms
        
    def send_metrics(self, fps, frame_number, timestamp_ms):
        """Send metrics to external system"""
        metrics_data = {
            'component': 'publisher',
            'fps': fps,
            'frame_number': frame_number,
            'timestamp_ms': timestamp_ms,
            'timestamp': datetime.now().isoformat()
        }
        
        self.metrics_reporter.send_metrics(metrics_data)
        
    def start(self):
        """Start the publisher"""
        try:
            self.setup_camera()
            self.setup_ffmpeg_rtsp()
            self.running = True
            
            self.log("Publisher started successfully")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    self.log("Failed to read frame from camera")
                    break
                
                # Add timestamp overlay
                frame_with_overlay, timestamp_ms = self.add_timestamp_overlay(frame)
                
                # Stream to FFmpeg
                try:
                    self.ffmpeg_process.stdin.write(frame_with_overlay.tobytes())
                except BrokenPipeError:
                    self.log("FFmpeg process terminated")
                    break
                
                # Update metrics
                self.calculate_fps()
                self.frame_number += 1
                
                # Send metrics every 30 frames
                if self.frame_number % 30 == 0:
                    self.send_metrics(self.current_fps, self.frame_number, timestamp_ms)
                
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            self.log("Publisher stopped by user")
        except Exception as e:
            self.log(f"Publisher error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the publisher with proper cleanup"""
        if not self.running:
            return
            
        self.log("Stopping publisher...")
        self.running = False
        
        # Stop FFmpeg
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait(timeout=5)
                self.log("FFmpeg terminated gracefully")
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.terminate()
                try:
                    self.ffmpeg_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.ffmpeg_process.kill()
                self.log("FFmpeg force terminated")
            except Exception as e:
                self.log(f"FFmpeg cleanup error: {e}")
            finally:
                self.ffmpeg_process = None
        
        # Release camera
        if self.cap:
            try:
                self.cap.release()
                cv2.destroyAllWindows()
                time.sleep(1)
                self.log("Camera released")
            except Exception as e:
                self.log(f"Camera release error: {e}")
            finally:
                self.cap = None
                
        self.log("Publisher stopped")