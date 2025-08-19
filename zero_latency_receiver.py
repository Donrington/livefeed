#!/usr/bin/env python3
import sys
import os
import cv2
import time
import re
import signal
import atexit
import socket
import argparse
from datetime import datetime

class ZeroLatencyReceiver:
    def __init__(self, rtsp_url=None, display_mode="headless"):
        self.name = "ZeroLatencyReceiver"
        self.running = False
        self.display_mode = display_mode  # "headless", "display", or "save"
        
        """ Get the local IP address to construct the RTSP URL if not provided."""
        if rtsp_url is None:
            local_ip = ZeroLatencyReceiver.get_local_ip()
            self.rtsp_url = f"rtsp://{local_ip}:8554/zerolatency"
            ZeroLatencyReceiver.log(f"Auto-detected IP for RTSP: {local_ip}")
        else:
            self.rtsp_url = rtsp_url
            
        ZeroLatencyReceiver.log(f"RTSP URL: {self.rtsp_url}")
        
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
    
    """Added static method for IP detection - same as publisher"""
    @staticmethod 
    def get_local_ip():
        """Simple static method to get local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "localhost"
    
    """Added static method for logging - same as publisher"""        
    @staticmethod   
    def log(message):
        """Static method to log messages with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] ZeroLatencyReceiver: {message}")
    
    """Added static method to check if server is available"""
    @staticmethod     
    def check_rtsp_server(host, port):
        """Static method to check if RTSP server is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    """Added static method to build RTSP URLs"""
    @staticmethod
    def build_rtsp_url(ip, port, stream_name):
        """Static method to build RTSP URL"""
        return f"rtsp://{ip}:{port}/{stream_name}"
        
    def signal_handler(self, sig, frame):
        ZeroLatencyReceiver.log("Received interrupt signal, shutting down...")
        self.stop()
        sys.exit(0)
        
    def setup_rtsp_connection(self):
        """Setup RTSP connection with Raspberry Pi optimizations"""
        ZeroLatencyReceiver.log(f"Connecting to RTSP stream: {self.rtsp_url}")
        
        # Extract host and port from RTSP URL for connectivity check
        try:
            # Parse rtsp://host:port/stream format
            url_parts = self.rtsp_url.replace('rtsp://', '').split('/')
            host_port = url_parts[0].split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 8554
            
            # Check if RTSP server is reachable
            if not ZeroLatencyReceiver.check_rtsp_server(host, port):
                ZeroLatencyReceiver.log(f"Warning: Cannot reach RTSP server at {host}:{port}")
            else:
                ZeroLatencyReceiver.log(f"RTSP server at {host}:{port} is reachable")
                
        except Exception as e:
            ZeroLatencyReceiver.log(f"Could not parse RTSP URL for connectivity check: {e}")
        
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
                    ZeroLatencyReceiver.log(f"Successfully connected using backend: {backend_name}")
                    
                    # Get stream properties
                    width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = self.cap.get(cv2.CAP_PROP_FPS)
                    
                    ZeroLatencyReceiver.log(f"Stream properties: {width}x{height} @ {fps} FPS")
                    return True
                    
            except Exception as e:
                ZeroLatencyReceiver.log(f"Failed to connect with backend {backend}: {e}")
                continue
        
        ZeroLatencyReceiver.log("Failed to connect to RTSP stream with any backend")
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
        
        # Extract IP from RTSP URL for display
        try:
            url_parts = self.rtsp_url.replace('rtsp://', '').split('/')
            host_port = url_parts[0]
            ip_text = f"SRC: {host_port}"
        except:
            ip_text = "SRC: Unknown"
        
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
        cv2.putText(frame, ip_text, (x_pos, 100), font, 0.4, color, thickness)
        
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
                ZeroLatencyReceiver.log(f"Saving video to: {filename}")
                return True
            else:
                ZeroLatencyReceiver.log("Failed to setup video writer")
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
                    ZeroLatencyReceiver.log("User pressed 'q', stopping...")
                    return False
            except cv2.error:
                # No display available, switch to headless mode
                ZeroLatencyReceiver.log("No display available, switching to headless mode")
                self.display_mode = "headless"
                
        elif self.display_mode == "save" and self.video_writer:
            # Save frame to video file
            self.video_writer.write(frame_with_overlay)
            
        # In headless mode, just log progress occasionally
        if self.display_mode == "headless" and self.frame_count % 150 == 0:  # Every 5 seconds at 30fps
            ZeroLatencyReceiver.log(f"Processed {self.frame_count} frames, FPS: {self.current_fps:.1f}, Latency: {self.latency_ms:.1f}ms")
            
        return True
        
    def start(self):
        """Start the receiver"""
        if not self.setup_rtsp_connection():
            ZeroLatencyReceiver.log("Failed to setup RTSP connection")
            return False
            
        self.running = True
        ZeroLatencyReceiver.log("Receiver started")
        ZeroLatencyReceiver.log(f"Display mode: {self.display_mode}")
        ZeroLatencyReceiver.log(f"Receiving from: {self.rtsp_url}")
        
        # Initialize video writer if needed
        first_frame = True
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    ZeroLatencyReceiver.log("Failed to read frame, retrying...")
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
            ZeroLatencyReceiver.log("Interrupted by user")
        except Exception as e:
            ZeroLatencyReceiver.log(f"Error during operation: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the receiver and cleanup"""
        if not self.running:
            return
            
        self.running = False
        
        if self.cap:
            self.cap.release()
            ZeroLatencyReceiver.log("Released video capture")
            
        if self.video_writer:
            self.video_writer.release()
            ZeroLatencyReceiver.log("Released video writer")
            
        if self.display_mode == "display":
            cv2.destroyAllWindows()
            
        ZeroLatencyReceiver.log(f"Stopped. Total frames processed: {self.frame_count}")

def main():
    parser = argparse.ArgumentParser(description='Zero Latency RTSP Receiver with IP Auto-Detection')
    parser.add_argument('--rtsp-url', '-u', 
                       default=None,
                       help='RTSP URL to receive from (auto-detected if not specified)')
    parser.add_argument('--display-mode', '-d',
                       choices=['headless', 'display', 'save'],
                       default='headless',
                       help='Display mode: headless (no display), display (show window), save (save to file)')
    parser.add_argument('--test-connection', '-t',
                       action='store_true',
                       help='Test connection to auto-detected IP and exit')
    
    args = parser.parse_args()
    
    # Test connection mode
    if args.test_connection:
        local_ip = ZeroLatencyReceiver.get_local_ip()
        print(f"Auto-detected IP: {local_ip}")
        print(f"Testing RTSP server connectivity...")
        
        # Test local IP
        if ZeroLatencyReceiver.check_rtsp_server(local_ip, 8554):
            print(f"✅ RTSP server reachable at {local_ip}:8554")
        else:
            print(f"❌ RTSP server not reachable at {local_ip}:8554")
        
        # Test VPN IP if different
        if local_ip != "10.8.0.1":
            if ZeroLatencyReceiver.check_rtsp_server("10.8.0.1", 8554):
                print(f"✅ RTSP server reachable via VPN at 10.8.0.1:8554")
            else:
                print(f"❌ RTSP server not reachable via VPN at 10.8.0.1:8554")
        
        return
    
    # Check if display is available when display mode is requested
    if args.display_mode == 'display':
        if not os.environ.get('DISPLAY'):
            print("Warning: No DISPLAY environment variable found. Switching to headless mode.")
            args.display_mode = 'headless'
    
    receiver = ZeroLatencyReceiver(rtsp_url=args.rtsp_url, display_mode=args.display_mode)
    receiver.start()

if __name__ == "__main__":
    main()