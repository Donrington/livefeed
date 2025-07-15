# streaming/receiver.py
import cv2
import time
import sys
import os
from datetime import datetime

# Django setup for standalone execution
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'live_feed.settings')
    import django
    django.setup()

from base import BaseStreamComponent

class HLSReceiver(BaseStreamComponent):
    def __init__(self):
        super().__init__("Receiver")
        self.cap = None
        
    def setup_stream(self):
        # Initialize HLS stream capture
        hls_url = self.config.get_hls_url()
        self.log(f"Connecting to HLS stream: {hls_url}")
        
        self.cap = cv2.VideoCapture(hls_url)
        if not self.cap.isOpened():
            raise Exception(f"Could not open stream {hls_url}")
            
        # Minimize buffer for low latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
    def add_receiver_overlay(self, frame, latency_ms=None):
    #    Add red receiver overlay
        current_time = datetime.now()
        
        timestamp_text = f"REC: {current_time.strftime('%H:%M:%S.%f')[:-3]}"
        fps_text = f"REC FPS: {self.current_fps:.1f}"
        latency_text = f"Latency: {latency_ms:.1f}ms" if latency_ms else "Latency: --"
        
        # Red color overlay (positioned on right)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        red_color = (0, 0, 255)  # Red in BGR
        
        height, width = frame.shape[:2]
        
        cv2.putText(frame, timestamp_text, (width - 300, 30), font, font_scale, red_color, thickness)
        cv2.putText(frame, fps_text, (width - 300, 60), font, font_scale, red_color, thickness)
        cv2.putText(frame, latency_text, (width - 300, 90), font, font_scale, red_color, thickness)
        
        return frame
        
    def calculate_latency(self):
    #    Calculate latency from latest database record
        try:
            from app.models import StreamMetrics
            latest_metric = StreamMetrics.objects.filter(
                publisher_fps__gt=0
            ).order_by('-id').first()
            
            if latest_metric:
                # Calculate time difference
                current_time = time.time() * 1000
                db_time = latest_metric.timestamp.timestamp() * 1000
                latency = current_time - db_time
                
                # Update the record with receiver data
                latest_metric.receiver_fps = self.current_fps
                latest_metric.latency_ms = latency
                latest_metric.save()
                
                return latency
        except Exception as e:
            self.log(f"Failed to calculate latency: {e}")
            
        return None
        
    def start(self):
        # Start the receiver
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
                
                # Display frame for monitoring
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
    #   Stop the receiver
        self.running = False
        
        if self.cap:
            self.cap.release()
            self.log("Stream capture released")
            
        cv2.destroyAllWindows()

# Standalone execution
if __name__ == "__main__":
    receiver = HLSReceiver()
    try:
        receiver.start()
    except Exception as e:
        print(f"Receiver error: {e}")
    finally:
        receiver.stop()
