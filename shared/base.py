
from abc import ABC, abstractmethod
import time
import requests
import json
from datetime import datetime

class StreamComponent(ABC):
    """Base class for all streaming components"""
    
    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
        self.running = False
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0
        
    def calculate_fps(self):
        """Calculate current FPS"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_timer)
            self.fps_counter = 0
            self.fps_timer = current_time
            
    def log(self, message):
        """Log with timestamp and component name"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"[{timestamp}] {self.name}: {message}")
        
    @abstractmethod
    def start(self):
        """Start the component"""
        pass
        
    @abstractmethod
    def stop(self):
        """Stop the component"""
        pass

class MetricsReporter(ABC):
    """Base class for sending metrics to external systems"""
    
    @abstractmethod
    def send_metrics(self, metrics_data):
        """Send metrics to external system"""
        pass

class HTTPMetricsReporter(MetricsReporter):
    """HTTP API metrics reporter"""
    
    def __init__(self, api_url):
        self.api_url = api_url
        
    def send_metrics(self, metrics_data):
        """Send metrics via HTTP POST"""
        try:
            response = requests.post(
                self.api_url,
                json=metrics_data,
                timeout=2
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send metrics: {e}")
            return False

class NullMetricsReporter(MetricsReporter):
    """No-op metrics reporter for testing"""
    
    def send_metrics(self, metrics_data):
        """Do nothing - for testing without API"""
        print(f"Metrics (not sent): {metrics_data}")
        return True