import sys
import cv2
import subprocess
import time
import signal
import atexit
import socket
from datetime import datetime

class ZeroLatencyPublisher:
    def __init__(self):
        self.running = False
        self.camera_index = 0
        self.width = 640
        self.height = 480
        self.target_fps = 30
        self.bitrate = '800k'
        self.rtsp_url = "rtsp://localhost:8554/zerolatency"
        
        self.cap = None
        self.ffmpeg_process = None
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
            self.log("MediaMTX not running on port 8554")
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
            
        self.log("Stopped")

if __name__ == "__main__":
    publisher = ZeroLatencyPublisher()
    publisher.start()