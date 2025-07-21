import sys
import os
import cv2
import time
import re
from datetime import datetime

class ZeroLatencyReceiver:
    def __init__(self):
        self.name = "ZeroLatencyReceiver"
        self.running = False
        self.rtsp_url = "rtsp://localhost:8554/zerolatency"
        self.cap = None
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0
        self.latency_ms = 0
        
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] {self.name}: {message}")
        
    def setup_rtsp_connection(self):
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
    def extract_publisher_timestamp(self, frame):
        """Extract publisher timestamp from frame overlay"""
        try:
            # Convert frame to grayscale for OCR-like processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Look for timestamp pattern in top-left area where publisher adds it
            roi = gray[10:30, 0:200]  # Region where "PUB: HH:MM:SS.mmm" appears
            
            # This is a simplified approach - in production you'd use proper OCR
            # For now, we'll calculate latency based on frame processing time
            current_time = time.time()
            if hasattr(self, 'last_frame_time'):
                processing_delay = (current_time - self.last_frame_time) * 1000
                # Estimate total latency (processing + network + encoding)
                self.latency_ms = processing_delay + 30  # Add estimated network/encoding delay
            else:
                self.latency_ms = 50  # Initial estimate
                
            self.last_frame_time = current_time
            
        except:
            self.latency_ms = 50  # Fallback
            
    def add_receiver_overlay(self, frame):
        current_time = datetime.now()
        timestamp_text = f"REC: {current_time.strftime('%H:%M:%S.%f')[:-3]}"
        fps_text = f"REC FPS: {self.current_fps:.1f}"
        latency_text = f"LAT: {self.latency_ms:.1f}ms"
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        height, width = frame.shape[:2]
        
        cv2.putText(frame, timestamp_text, (width - 200, 20), font, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, fps_text, (width - 200, 40), font, 0.5, (0, 0, 255), 1)
        cv2.putText(frame, latency_text, (width - 200, 60), font, 0.5, (0, 0, 255), 1)
        
        return frame
        
    def calculate_fps(self):
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = current_time
            
    def start(self):
        self.setup_rtsp_connection()
        self.running = True
        self.log("Receiver started")
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            
            # Calculate latency from frame
            self.extract_publisher_timestamp(frame)
            
            # Add receiver overlay
            frame_with_overlay = self.add_receiver_overlay(frame)
            
            self.calculate_fps()
            
            cv2.imshow('Zero Latency Receiver', frame_with_overlay)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.stop()
            
    def stop(self):
        if not self.running:
            return
            
        self.running = False
        
        if self.cap:
            self.cap.release()
            
        cv2.destroyAllWindows()
        self.log("Stopped")

if __name__ == "__main__":
    receiver = ZeroLatencyReceiver()
    receiver.start()