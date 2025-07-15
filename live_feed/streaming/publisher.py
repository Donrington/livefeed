
# streaming/publisher.py
import cv2
import numpy as np
import subprocess
import sys
import os
import time
from datetime import datetime

# Django setup for standalone execution
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'live_feed.settings')
    import django
    django.setup()

from base import BaseStreamComponent

class RTSPPublisher(BaseStreamComponent):
    def __init__(self):
        super().__init__("Publisher")
        self.cap = None
        self.ffmpeg_process = None
        self.frame_number = 0
        
    def setup_camera(self):
        # Initialize camera capture with optimized settings
        self.log("Setting up camera...")
        self.cap = cv2.VideoCapture(self.config.camera_index)
        
        if not self.cap.isOpened():
            raise Exception(f"Could not open camera {self.config.camera_index}")
        
        # Optimize camera settings for low latency
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.video_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.video_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.config.video_fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer
        
        self.log(f"Camera setup: {self.config.video_width}x{self.config.video_height}@{self.config.video_fps}fps")
        
    def setup_ffmpeg_rtsp(self):
        # Setup FFmpeg process for RTSP streaming
        rtsp_url = self.config.get_rtsp_url()
        self.log(f"Setting up FFmpeg stream to {rtsp_url}")
        
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
            rtsp_url
        ]
        
        self.ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
    def add_timestamp_overlay(self, frame):
        # Add blue timestamp overlay
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
        blue_color = (255, 0, 0)  # Blue in BGR
        
        cv2.putText(frame, timestamp_text, (10, 30), font, font_scale, blue_color, thickness)
        cv2.putText(frame, fps_text, (10, 60), font, font_scale, blue_color, thickness)
        cv2.putText(frame, frame_text, (10, 90), font, font_scale, blue_color, thickness)
        
        return frame, timestamp_ms
        
    def save_metrics_to_db(self, fps, frame_number):
    #    Save metrics directly to Django database
        try:
            from app.models import StreamMetrics
            StreamMetrics.objects.create(
                publisher_fps=fps,
                frame_number=frame_number,
                receiver_fps=0,
                latency_ms=0
            )
        except Exception as e:
            self.log(f"Failed to save metrics to DB: {e}")
            
    def start(self):
    #   Start the publisher
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
                
                # Stream frame to FFmpeg
                try:
                    self.ffmpeg_process.stdin.write(frame_with_overlay.tobytes())
                except BrokenPipeError:
                    self.log("FFmpeg process terminated")
                    break
                
                # Update metrics
                self.calculate_fps()
                self.frame_number += 1
                
                # Save metrics every 30 frames
                if self.frame_number % 30 == 0:
                    self.save_metrics_to_db(self.current_fps, self.frame_number)
                
                time.sleep(0.001)  # Small delay
                
        except KeyboardInterrupt:
            self.log("Publisher stopped by user")
        except Exception as e:
            self.log(f"Publisher error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        # Stop the publisher
        self.running = False
        
        if self.cap:
            self.cap.release()
            self.log("Camera released")
            
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait(timeout=5)
            except:
                self.ffmpeg_process.terminate()
            self.log("FFmpeg process terminated")

# Standalone execution
if __name__ == "__main__":
    publisher = RTSPPublisher()
    try:
        publisher.start()
    except Exception as e:
        print(f"Publisher error: {e}")
    finally:
        publisher.stop()

