
# receiver/main.py (UPDATED)
import sys
import os

# Add the parent directory to Python path so we can import 'shared'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from shared.base import HTTPMetricsReporter, NullMetricsReporter, StreamComponent

import cv2
import time
import signal
import atexit
import requests
from datetime import datetime

class HLSReceiver(StreamComponent):
    """Standalone HLS Receiver - No Django dependency"""
    
    def __init__(self, config=None, metrics_reporter=None):
        super().__init__("Receiver")
        self.config = config or self.default_config()
        self.metrics_reporter = metrics_reporter or NullMetricsReporter()
        self.cap = None
        
        # Register cleanup handlers
        atexit.register(self.emergency_cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def default_config(self):
        """Default configuration if no config provided"""
        class DefaultConfig:
            hls_url = 'http://localhost:8888/mystream/index.m3u8'
            metrics_api_url = 'http://localhost:8000/api/metrics/receiver/'
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
        
    def setup_stream(self):
        """Initialize HLS stream capture"""
        self.log(f"Connecting to HLS stream: {self.config.hls_url}")
        
        self.cap = cv2.VideoCapture(self.config.hls_url)
        if not self.cap.isOpened():
            raise Exception(f"Could not open stream {self.config.hls_url}")
            
        # Minimize buffer for low latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
    def add_receiver_overlay(self, frame, latency_ms=None):
        """Add red receiver overlay"""
        current_time = datetime.now()
        
        timestamp_text = f"REC: {current_time.strftime('%H:%M:%S.%f')[:-3]}"
        fps_text = f"REC FPS: {self.current_fps:.1f}"
        latency_text = f"Latency: {latency_ms:.1f}ms" if latency_ms else "Latency: --"
        
        # Red color overlay (positioned on right)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        red_color = (0, 0, 255)  # BGR
        
        height, width = frame.shape[:2]
        
        cv2.putText(frame, timestamp_text, (width - 300, 30), font, font_scale, red_color, thickness)
        cv2.putText(frame, fps_text, (width - 300, 60), font, font_scale, red_color, thickness)
        cv2.putText(frame, latency_text, (width - 300, 90), font, font_scale, red_color, thickness)
        
        return frame
        
    def calculate_latency(self):
        """Calculate latency by requesting latest publisher metrics"""
        try:
            response = requests.get(
                'http://localhost:8000/api/metrics/latest/',
                timeout=1
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'timestamp' in data:
                    current_time = time.time() * 1000
                    publisher_time = datetime.fromisoformat(data['timestamp']).timestamp() * 1000
                    latency = current_time - publisher_time
                    return latency
                    
        except Exception as e:
            self.log(f"Failed to calculate latency: {e}")
            
        return None
        
    def send_metrics(self, fps, latency_ms):
        """Send receiver metrics to external system"""
        metrics_data = {
            'component': 'receiver',
            'fps': fps,
            'latency_ms': latency_ms,
            'timestamp': datetime.now().isoformat()
        }
        
        self.metrics_reporter.send_metrics(metrics_data)
        
    def start(self):
        """Start the receiver"""
        try:
            self.setup_stream()
            self.running = True
            frame_count = 0
            
            self.log("Receiver started successfully")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    self.log("Failed to read frame from stream")
                    time.sleep(0.1)
                    continue
                
                # Calculate latency
                latency_ms = self.calculate_latency()
                
                # Add receiver overlay
                frame_with_overlay = self.add_receiver_overlay(frame, latency_ms)
                
                # Update metrics
                self.calculate_fps()
                frame_count += 1
                
                # Send metrics every 30 frames
                if frame_count % 30 == 0 and latency_ms is not None:
                    self.send_metrics(self.current_fps, latency_ms)
                
                # Display frame
                cv2.imshow('Receiver Monitor', frame_with_overlay)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            self.log("Receiver stopped by user")
        except Exception as e:
            self.log(f"Receiver error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the receiver with proper cleanup"""
        if not self.running:
            return
            
        self.log("Stopping receiver...")
        self.running = False
        
        if self.cap:
            try:
                self.cap.release()
                self.log("Stream capture released")
            except Exception as e:
                self.log(f"Stream cleanup error: {e}")
            finally:
                self.cap = None
                
        cv2.destroyAllWindows()
        self.log("Receiver stopped")