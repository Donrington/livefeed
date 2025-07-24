import sys
import cv2
import subprocess
import time
import signal
import atexit
import socket
import os
import argparse
from datetime import datetime

class ZeroLatencyPublisher:
    def __init__(self, mediamtx_path):
        self.running = False
        self.camera_index = 0
        self.width = 640
        self.height = 480
        self.target_fps = 30
        self.bitrate = '800k'
        self.rtsp_url = "rtsp://localhost:8554/zerolatency"
        self.mediamtx_path = mediamtx_path
        
        self.cap = None
        self.ffmpeg_process = None
        self.mediamtx_process = None
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0
        
        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] {message}")
        
    def check_mediamtx(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 8554))
            sock.close()
            return result == 0
        except:
            return False
    
    def start_mediamtx(self):
        if not os.path.exists(self.mediamtx_path):
            self.log(f"MediaMTX executable not found at {self.mediamtx_path}")
            return False
            
        try:
            self.log("Starting MediaMTX...")
            self.mediamtx_process = subprocess.Popen(
                [self.mediamtx_path],
                cwd=os.path.dirname(self.mediamtx_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for MediaMTX to start up
            for i in range(10):
                time.sleep(1)
                if self.check_mediamtx():
                    self.log("MediaMTX started successfully")
                    return True
                self.log(f"Waiting for MediaMTX to start... ({i+1}/10)")
            
            self.log("MediaMTX failed to start within 10 seconds")
            return False
            
        except Exception as e:
            self.log(f"Error starting MediaMTX: {e}")
            return False
    
    def stop_mediamtx(self):
        if self.mediamtx_process:
            try:
                self.log("Stopping MediaMTX...")
                self.mediamtx_process.terminate()
                self.mediamtx_process.wait(timeout=5)
                self.log("MediaMTX stopped")
            except subprocess.TimeoutExpired:
                self.log("Force killing MediaMTX...")
                self.mediamtx_process.kill()
            except Exception as e:
                self.log(f"Error stopping MediaMTX: {e}")
            finally:
                self.mediamtx_process = None
    
    def setup_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
    def setup_ffmpeg(self):
        cmd = [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'bgr24',
            '-s', f'{self.width}x{self.height}', '-r', str(self.target_fps), '-i', '-',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
            '-g', '10', '-b:v', self.bitrate, '-maxrate', self.bitrate,
            '-bufsize', '200k', '-f', 'rtsp', '-rtsp_transport', 'tcp', self.rtsp_url
        ]
        
        self.ffmpeg_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        
    def add_timestamp(self, frame):
        current_time = datetime.now()
        timestamp = current_time.strftime('%H:%M:%S.%f')[:-3]
        
        # Calculate latency (time since frame capture)
        frame_time = time.time()
        latency_ms = (frame_time - getattr(self, 'frame_start_time', frame_time)) * 1000
        self.frame_start_time = frame_time
        
        cv2.putText(frame, f"PUB: {timestamp}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"LAT: {latency_ms:.1f}ms", (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return frame
        
    def calculate_fps(self):
        self.fps_counter += 1
        current_time = time.time()
        if current_time - self.fps_timer >= 2.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = current_time
            
    def start(self):
        if not self.check_mediamtx():
            self.log("MediaMTX not running, attempting to start...")
            if not self.start_mediamtx():
                self.log("Failed to start MediaMTX")
                return
            
        self.setup_camera()
        self.setup_ffmpeg()
        
        self.running = True
        self.log("Publisher started")
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame_with_timestamp = self.add_timestamp(frame)
            
            try:
                self.ffmpeg_process.stdin.write(frame_with_timestamp.tobytes())
                self.ffmpeg_process.stdin.flush()
            except:
                break
                
            self.calculate_fps()
            
    def signal_handler(self, sig, frame):
        self.stop()
        sys.exit(0)
        
    def stop(self):
        if not self.running:
            return
            
        self.running = False
        
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait()
            
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            
        self.stop_mediamtx()
        self.log("Stopped")

def main():
    parser = argparse.ArgumentParser(description='Zero Latency RTSP Publisher')
    parser.add_argument('--mediamtx-path', '-m', 
                       required=True,
                       help='Path to the MediaMTX executable')
    parser.add_argument('--camera-index', '-c', 
                       type=int, 
                       default=0,
                       help='Camera index to use (default: 0)')
    parser.add_argument('--width', '-w', 
                       type=int, 
                       default=640,
                       help='Video width (default: 640)')
    parser.add_argument('--height', '-ht', 
                       type=int, 
                       default=480,
                       help='Video height (default: 480)')
    parser.add_argument('--fps', '-f', 
                       type=int, 
                       default=30,
                       help='Target FPS (default: 30)')
    parser.add_argument('--bitrate', '-b', 
                       default='800k',
                       help='Video bitrate (default: 800k)')
    parser.add_argument('--rtsp-url', '-u', 
                       default='rtsp://localhost:8554/zerolatency',
                       help='RTSP URL to publish to (default: rtsp://localhost:8554/zerolatency)')
    
    args = parser.parse_args()
    
    publisher = ZeroLatencyPublisher(args.mediamtx_path)
    publisher.camera_index = args.camera_index
    publisher.width = args.width
    publisher.height = args.height
    publisher.target_fps = args.fps
    publisher.bitrate = args.bitrate
    publisher.rtsp_url = args.rtsp_url
    
    publisher.start()

if __name__ == "__main__":
    main()