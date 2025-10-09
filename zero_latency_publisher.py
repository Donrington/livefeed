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
from live_feed.app.config import NetworkConfig
import asyncio
from asyncio.exceptions import TimeoutError
import websockets
from websockets.exceptions import InvalidStatusCode
from asyncio.exceptions import TimeoutError
import queue
import asyncio
import threading
from live_feed.messages import messages_pb2
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s"
)
log = logging.getLogger(__name__) 

to_async_queue =  queue.Queue()   # main thread -> async thread
cam_status = messages_pb2.CameraStatus()
publisher_instance = None  # Global reference to publisher for WebSocket callbacks

async def writer(ws: websockets.WebSocketClientProtocol, stop_event: asyncio.Event):
    while not stop_event.is_set():
        try: 
            message = await asyncio.to_thread( to_async_queue.get, timeout=3) #timeout is needed to prevent blocking
            await ws.send(message)
            #print(f"Sent message: {message}")
            to_async_queue.task_done()
        except queue.Empty:
            continue

async def reader(ws: websockets.WebSocketClientProtocol, stop_event: asyncio.Event):
    """
    Reader coroutine to handle incoming messages from the WebSocket server.
    Processes CameraSettingsCommand messages from Django.
    """
    global publisher_instance
    while not stop_event.is_set():
        try:
            async for message in ws:
                # Parse incoming protobuf message
                try:
                    cmd = messages_pb2.CameraSettingsCommand()
                    cmd.ParseFromString(message)

                    # Apply the setting change to the camera
                    if publisher_instance:
                        # For exposure, divide by 10 (protobuf sends int, camera expects float)
                        value = cmd.value / 10.0 if cmd.setting == 'exposure' else cmd.value
                        publisher_instance.update_camera_setting(cmd.setting, value)
                        log.info(f"Applied setting: {cmd.setting} = {value}")
                    else:
                        log.warning("Publisher instance not available")

                except Exception as parse_error:
                    log.error(f"Failed to parse command: {parse_error}")

        except websockets.ConnectionClosed:
            log.info("websocket connection closed")
            break
        except Exception as e:
            log.info(f"Error in reader task: {e}")
            break


# NEW: WebSocket handler with auto-reconnect
async def WebSocketHandler(stop_event: asyncio.Event ):
    uri = f"ws://{NetworkConfig.PI_VPN_IP}:{NetworkConfig.WEBSOCKET_PORT}/ws/camera/"
    log.info (f"connecting to {uri}")
    while not stop_event.is_set():
        try:
            async with websockets.connect(uri) as ws:
                log.info("WebSocket connected")
                #read incoming messages as concurrent background task
                reader_task = asyncio.create_task(reader(ws, stop_event))
                writer_task = asyncio.create_task(writer(ws, stop_event))
                done, pending = await asyncio.wait(
                    {reader_task, writer_task, asyncio.create_task(stop_event.wait())},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                log.info("WebSocketHandler: Exiting main loop")
                # If stopping, close the socket politely
                if stop_event.is_set():
                    await ws.close(code=1000)

                # Cancel whatever is still pending
                for t in pending:
                    t.cancel()

                # Surface unexpected exceptions from finished tasks
                for t in done:
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass
                
        except InvalidStatusCode as e:
            log.error(f"Invalid status code: {e}")
        except TimeoutError:
            log.error("Connection timed out")
        except Exception as e:
            log.error(f"Connection error: {e}")
        
        log.info ("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)  

def run_asyncio_loop(publisher ):
    #wait until publisher is running before starting websocket
    while not publisher.isRunning():
        time.sleep(0.5)
    log.info("started websocket thread")
    stop_event = asyncio.Event()
    try:
        asyncio.run(WebSocketHandler(stop_event))
    except KeyboardInterrupt:
        log.info ("KeyboardInterrupt received, stopping...")
        stop_event.set()



class ZeroLatencyPublisher:
    def __init__(self, mediamtx_path, ffmpeg_path, camera_index, width, height, target_fps, bitrate, rtsp_url):
        self.running = False
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.bitrate = bitrate
        self.rtsp_url = rtsp_url
        self.mediamtx_path = mediamtx_path
        self.ffmpeg_path = ffmpeg_path
        self.lock = threading.Lock()
        self.cam_status = messages_pb2.CameraStatus()
        self.cam_status.isConnected = False

        
        """ Get the local IP address to construct the RTSP URL."""
        """Use configuration from NetworkConfig"""
        # local_ip = self.get_local_ip()
        local_ip = NetworkConfig.PI_VPN_IP
        self.rtsp_url = f"rtsp://{local_ip}:{NetworkConfig.RTSP_PORT}/{NetworkConfig.STREAM_NAME}"
        
        """ Initialize camera and ffmpeg process variables."""
        self.cap = None
        self.ffmpeg_process = None
        self.mediamtx_process = None
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0

        """ Initialize camera settings with default values."""
        self.camera_settings = {
            'brightness': 0,    # -130 to +130
        }
        self.settings_lock = threading.Lock()

        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self.signal_handler)
     
    def isRunning(self):
        with self.lock:
            return self.running
        
    def setRunning(self, value:bool):
        with self.lock:
            self.running = value
            
    """"removed self from get_local_ip to make it a static method"""     
    @staticmethod 
    def get_local_ip():
        """Simple method to get local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "localhost"

      
    @staticmethod     
    def check_mediamtx():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 8554))
            sock.close()
            return result == 0
        except:
            return False
    
    
    """"chnages self. to ZeroLatencyPublisher to make it a static method"""
    def start_mediamtx(self):
        if not os.path.exists(self.mediamtx_path):
            log.error(f"MediaMTX executable not found at {self.mediamtx_path}")
            return False
            
        try:
            log.info("Starting MediaMTX...")
            self.mediamtx_process = subprocess.Popen(
                [self.mediamtx_path],
                cwd=os.path.dirname(self.mediamtx_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for MediaMTX to start up
            for i in range(10):
                time.sleep(1)
                if ZeroLatencyPublisher.check_mediamtx():
                    log.info("MediaMTX started successfully")
                    return True
                log.info(f"Waiting for MediaMTX to start... ({i+1}/10)")
            
            log.info("MediaMTX failed to start within 10 seconds")
            return False
            
        except Exception as e:
            log.error(f"Error starting MediaMTX: {e}")
            return False
    
    def stop_mediamtx(self):
        if self.mediamtx_process:
            try:
                log.info("Stopping MediaMTX...")
                self.mediamtx_process.terminate()
                self.mediamtx_process.wait(timeout=5)
                log.info("MediaMTX stopped")
            except subprocess.TimeoutExpired:
                log.info("Force killing MediaMTX...")
                self.mediamtx_process.kill()
            except Exception as e:
                log.error(f"Error stopping MediaMTX: {e}")
            finally:
                self.mediamtx_process = None
    
    
    def setup_camera(self):

        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Apply initial camera settings
        self.apply_camera_settings()

    def apply_camera_settings(self):
        """Apply current camera settings to the camera"""
        if self.cap is None or not self.cap.isOpened():
            return

        with self.settings_lock:
            try:
                # Check camera's brightness capabilities
                min_brightness = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
                log.info(f"Camera default brightness: {min_brightness}")

                # Try to get brightness range (some cameras support this)
                try:
                    min_val = self.cap.get(cv2.CAP_PROP_BRIGHTNESS + 100)  # Some cameras use offset for min
                    max_val = self.cap.get(cv2.CAP_PROP_BRIGHTNESS + 200)  # Some cameras use offset for max
                    log.info(f"Brightness range (if supported): {min_val} to {max_val}")
                except:
                    log.info("Brightness range query not supported")

                # Set brightness
                result = self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.camera_settings['brightness'])
                actual = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)

                if result:
                    log.info(f"✓ Brightness set to {self.camera_settings['brightness']}, actual value: {actual}")
                else:
                    log.warning("✗ Camera does not support brightness control")

            except Exception as e:
                log.error(f"Error applying camera settings: {e}")

    def update_camera_setting(self, setting, value):
        """Update a specific camera setting"""
        with self.settings_lock:
            if setting == 'brightness' and setting in self.camera_settings:
                self.camera_settings[setting] = value
                log.info(f"Requested brightness: {value}")

                # Apply the setting immediately to camera
                if self.cap and self.cap.isOpened():
                    try:
                        # Get current brightness before setting
                        current = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
                        log.info(f"Current brightness before set: {current}")

                        # Set new brightness
                        result = self.cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

                        # Read back what was actually set
                        actual = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
                        log.info(f"Brightness after set: requested={value}, actual={actual}, success={result}")

                        if result:
                            log.info(f"✓ Brightness control applied")
                        else:
                            log.warning("✗ Camera does not support brightness control")
                    except Exception as e:
                        log.error(f"Error applying brightness: {e}")
            else:
                log.warning(f"Unknown or unsupported setting: {setting}")

    def send_camera_status(self):
        """Send current camera status including settings to Django"""
        with self.settings_lock:
            self.cam_status.isConnected = (self.cap is not None and self.cap.isOpened())
            self.cam_status.brightness = self.camera_settings['brightness']
            self.cam_status.fps = self.current_fps

        try:
            to_async_queue.put(self.cam_status.SerializeToString(), block=False)
        except queue.Full:
            log.warning("Queue full, skipping status update")
        
    def setup_ffmpeg(self):
        cmd = [
            self.ffmpeg_path, '-y', '-hide_banner', '-loglevel', 'error',
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
        
        """Added a Url log to indicate where the stream will be available"""
        log.info(f"Stream will be available at: {self.rtsp_url}")
        
        if not ZeroLatencyPublisher.check_mediamtx():
            log.info("MediaMTX not running, attempting to start...")
            if not self.start_mediamtx():
                log.error("Failed to start MediaMTX")
                return
            
        self.setup_camera()
        self.setup_ffmpeg()        
        self.setRunning(True)
        log.info("Starting publishing frames to client")
        
        while self.isRunning():
            ret, frame = self.cap.read()

            # Update camera status with current settings
            with self.settings_lock:
                self.cam_status.isConnected = ret
                self.cam_status.brightness = self.camera_settings['brightness']
                self.cam_status.fps = self.current_fps

            if not ret:
                continue
            else:
                to_async_queue.put(self.cam_status.SerializeToString()) # if full raises exception queue.Full
        
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
        if not self.isRunning():
            return
            
        self.setRunning(False)
        
        if self.ffmpeg_process:
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait()
            
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            
        self.stop_mediamtx()
        log.info("Stopped publishing frames to client")

def main():
    global publisher_instance

    parser = argparse.ArgumentParser(description='Zero Latency RTSP Publisher')
    parser.add_argument('--mediamtx-path', '-m',
                       required=True,
                       help='Path to the MediaMTX executable')
    parser.add_argument('--ffmpeg-path', '-f',
                       required=True,
                       help='Path to the ffmepg executable')
    parser.add_argument('--camera_index', '-c',
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
    parser.add_argument('--fps', '-fps',
                       type=int,
                       default=30,
                       help='Target FPS (default: 30)')
    parser.add_argument('--bitrate', '-b',
                       default='800k',
                       help='Video bitrate (default: 800k)')
    parser.add_argument('--rtsp-url', '-u',
                       default='rtsp://192.168.0.183:8554/zerolatency',
                       help='RTSP URL to publish to (default: rtsp://localhost:8554/zerolatency)')

    args = parser.parse_args()

    publisher = ZeroLatencyPublisher(
        args.mediamtx_path,
        args.ffmpeg_path,
        args.camera_index,
        args.width,
        args.height,
        args.fps,
        args.bitrate,
        args.rtsp_url
    )

    # Set global reference for WebSocket callbacks
    publisher_instance = publisher

    async_thread = threading.Thread(target=run_asyncio_loop, args=(publisher, ), daemon=True)
    async_thread.start()
    publisher.start()
   
if __name__ == "__main__":
    main()

    

    
