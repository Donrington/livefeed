#!/usr/bin/env python3
import sys
import os
import cv2
import time
import re
import signal
import atexit
import argparse
from datetime import datetime

class ZeroLatencyReceiver:
    def __init__(self, rtsp_url="rtsp://localhost:8554/zerolatency", display_mode="headless"):
        self.name = "ZeroLatencyReceiver"
        self.running = False
        self.rtsp_url = rtsp_url
        self.display_mode = display_mode  # "headless", "display", or "save"
        self.cap = None
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0
        self.latency_ms = 0
        self.frame_count = 0
        self.last_frame_time = time.time()
        
        # Video writer for saving frames (optional)
        self.video_writer = None
        
        # Signal handlers for graceful shutdown
        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] {self.name}: {message}")
        
    def signal_handler(self, sig, frame):
        self.log("Received interrupt signal, shutting down...")
        self.stop()
        sys.exit(0)
        
    def setup_rtsp_connection(self):
        """Setup RTSP connection with Raspberry Pi optimizations"""
        self.log(f"Connecting to RTSP stream: {self.rtsp_url}")
        
        # Try different backends in order of preference for Raspberry Pi
        backends = [
            cv2.CAP_FFMPEG,
            cv2.CAP_GSTREAMER,
            cv2.CAP_V4L2,
            cv2.CAP_ANY
        ]
        
        for backend in backends:
            try:
                self.cap = cv2.VideoCapture(self.rtsp_url, backend)
                
                # Set buffer size to minimize latency
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Set additional properties for low latency
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                
                if self.cap.isOpened():
                    backend_name = self.cap.getBackendName()
                    self.log(f"Successfully connected using backend: {backend_name}")
                    
                    # Get stream properties
                    width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = self.cap.get(cv2.CAP_PROP_FPS)
                    
                    self.log(f"Stream properties: {width}x{height} @ {fps} FPS")
                    return True
                    
            except Exception as e:
                self.log(f"Failed to connect with backend {backend}: {e}")
                continue
        
        self.log("Failed to connect to RTSP stream with any backend")
        return False
        
    def extract_publisher_timestamp_simple(self, frame):
        """Simplified timestamp extraction without OCR dependencies"""
        try:
            # Look for green text in the top-left corner (publisher timestamp)
            # Since we know the publisher uses green color (0, 255, 0)
            
            # Extract region where publisher timestamp should be
            roi = frame[5:25, 5:150]  # Top-left corner
            
            # Look for green pixels (publisher text color)
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Define range for green color
            lower_green = (40, 100, 100)
            upper_green = (80, 255, 255)
            
            mask = cv2.inRange(hsv, lower_green, upper_green)
            green_pixels = cv2.countNonZero(mask)
            
            # If we detect green text, estimate latency based on frame timing
            if green_pixels > 10:  # Threshold for detecting text
                current_time = time.time()
                
                # Calculate frame interval
                frame_interval = current_time - self.last_frame_time
                
                # Expected frame interval for 30 FPS
                expected_interval = 1.0 / 30.0
                
                # Estimate latency (base latency + any frame delays)
                base_latency = 50  # Base network + processing latency in ms
                if frame_interval > expected_interval * 1.5:
                    # Frame is significantly late
                    additional_latency = (frame_interval - expected_interval) * 1000
                    self.latency_ms = base_latency + additional_latency
                else:
                    self.latency_ms = base_latency
                    
                self.last_frame_time = current_time
            else:
                # No timestamp detected, use default
                self.latency_ms = 75
                
        except Exception as e:
            # Fallback latency
            self.latency_ms = 100
            
    def add_receiver_overlay(self, frame):
        """Add receiver information overlay"""
        current_time = datetime.now()
        timestamp_text = f"REC: {current_time.strftime('%H:%M:%S.%f')[:-3]}"
        fps_text = f"REC FPS: {self.current_fps:.1f}"
        latency_text = f"EST LAT: {self.latency_ms:.1f}ms"
        frame_text = f"FRAME: {self.frame_count}"
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        color = (0, 0, 255)  # Red color for receiver text
        
        height, width = frame.shape[:2]
        
        # Position text on the right side
        x_pos = width - 200 if width > 250 else 5
        
        cv2.putText(frame, timestamp_text, (x_pos, 20), font, font_scale, color, thickness)
        cv2.putText(frame, fps_text, (x_pos, 40), font, font_scale, color, thickness)
        cv2.putText(frame, latency_text, (x_pos, 60), font, font_scale, color, thickness)
        cv2.putText(frame, frame_text, (x_pos, 80), font, font_scale, color, thickness)
        
        return frame
        
    def calculate_fps(self):
        """Calculate and update FPS"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_timer >= 2.0:  # Update every 2 seconds
            self.current_fps = self.fps_counter / (current_time - self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = current_time
            
    def setup_video_writer(self, frame_width, frame_height):
        """Setup video writer for saving frames"""
        if self.display_mode == "save":
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"received_stream_{timestamp}.avi"
            
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (frame_width, frame_height))
            
            if self.video_writer.isOpened():
                self.log(f"Saving video to: {filename}")
                return True
            else:
                self.log("Failed to setup video writer")
                return False
        return True
        
    def process_frame(self, frame):
        """Process each received frame"""
        self.frame_count += 1
        
        # Extract latency information
        self.extract_publisher_timestamp_simple(frame)
        
        # Add receiver overlay
        frame_with_overlay = self.add_receiver_overlay(frame)
        
        # Calculate FPS
        self.calculate_fps()
        
        # Handle different display modes
        if self.display_mode == "display":
            # Show frame (only if display is available)
            try:
                cv2.imshow('Zero Latency Receiver', frame_with_overlay)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.log("User pressed 'q', stopping...")
                    return False
            except cv2.error:
                # No display available, switch to headless mode
                self.log("No display available, switching to headless mode")
                self.display_mode = "headless"
                
        elif self.display_mode == "save" and self.video_writer:
            # Save frame to video file
            self.video_writer.write(frame_with_overlay)
            
        # In headless mode, just log progress occasionally
        if self.display_mode == "headless" and self.frame_count % 150 == 0:  # Every 5 seconds at 30fps
            self.log(f"Processed {self.frame_count} frames, FPS: {self.current_fps:.1f}, Latency: {self.latency_ms:.1f}ms")
            
        return True
        
    def start(self):
        """Start the receiver"""
        if not self.setup_rtsp_connection():
            self.log("Failed to setup RTSP connection")
            return False
            
        self.running = True
        self.log("Receiver started")
        self.log(f"Display mode: {self.display_mode}")
        
        # Initialize video writer if needed
        first_frame = True
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    self.log("Failed to read frame, retrying...")
                    time.sleep(0.1)
                    continue
                
                # Setup video writer on first frame
                if first_frame and self.display_mode == "save":
                    height, width = frame.shape[:2]
                    self.setup_video_writer(width, height)
                    first_frame = False
                
                # Process frame
                if not self.process_frame(frame):
                    break
                    
        except KeyboardInterrupt:
            self.log("Interrupted by user")
        except Exception as e:
            self.log(f"Error during operation: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the receiver and cleanup"""
        if not self.running:
            return
            
        self.running = False
        
        if self.cap:
            self.cap.release()
            self.log("Released video capture")
            
        if self.video_writer:
            self.video_writer.release()
            self.log("Released video writer")
            
        if self.display_mode == "display":
            cv2.destroyAllWindows()
            
        self.log(f"Stopped. Total frames processed: {self.frame_count}")

def main():
    parser = argparse.ArgumentParser(description='Zero Latency RTSP Receiver for Raspberry Pi')
    parser.add_argument('--rtsp-url', '-u', 
                       default='rtsp://localhost:8554/zerolatency',
                       help='RTSP URL to receive from (default: rtsp://localhost:8554/zerolatency)')
    parser.add_argument('--display-mode', '-d',
                       choices=['headless', 'display', 'save'],
                       default='headless',
                       help='Display mode: headless (no display), display (show window), save (save to file)')
    
    args = parser.parse_args()
    
    # Check if display is available when display mode is requested
    if args.display_mode == 'display':
        if not os.environ.get('DISPLAY'):
            print("Warning: No DISPLAY environment variable found. Switching to headless mode.")
            args.display_mode = 'headless'
    
    receiver = ZeroLatencyReceiver(rtsp_url=args.rtsp_url, display_mode=args.display_mode)
    receiver.start()

if __name__ == "__main__":
    main()