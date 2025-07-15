
# streaming/base.py
import cv2
import time
import threading
import requests
import json
from datetime import datetime
from abc import ABC, abstractmethod

class BaseStreamComponent(ABC):
    # Base class for streaming components
    
    def __init__(self, name):
        self.name = name
        from config import StreamingConfig
        self.config = StreamingConfig()
        self.running = False
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0
        
    def calculate_fps(self):
        # Calculate current FPS
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = current_time
            
    def log(self, message):
    #    Log with timestamp and component name
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] {self.name}: {message}")
        
    @abstractmethod
    def start(self):
        # Start the component
        pass
        
    @abstractmethod
    def stop(self):
        # Stop the component
        pass

