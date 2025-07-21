import sys
import os
# CRITICAL: We're inside publisher/ folder, need to go UP to find shared/
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)  # publisher/ folder
parent_dir = os.path.dirname(current_dir)    # root/ folder (where shared/ is)

# Add the PARENT directory to Python path
sys.path.insert(0, parent_dir)

print(f"📄 Current file: {current_file}")
print(f"📁 Current dir: {current_dir}")
print(f"📁 Parent dir: {parent_dir}")
print(f"🐍 Added to path: {parent_dir}")

# Now we can import from shared/ (which is in parent_dir)
try:
    from shared.base import HTTPMetricsReporter, NullMetricsReporter
    print("✅ Successfully imported from shared.base")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"📂 Parent directory contents: {os.listdir(parent_dir)}")
    sys.exit(1)

# Import from local main.py (in same publisher/ folder)
from main import RTSPPublisher

class PublisherConfig:
    """Configuration for standalone publisher"""
    
    def __init__(self, config_file=None):
        # Default configuration
        self.camera_index = 0
        self.video_width = 1280
        self.video_height = 720
        self.video_fps = 30
        self.video_bitrate = '1200k'
        self.gop_size = 15
        self.ffmpeg_preset = 'ultrafast'
        self.ffmpeg_tune = 'zerolatency'
        self.rtsp_url = 'rtsp://localhost:8554/mystream'
        self.metrics_api_url = 'http://localhost:8000/api/metrics/publisher/'
        
        # Try to load config file from parent directory
        if config_file:
            config_path = os.path.join(parent_dir, config_file)
            if os.path.exists(config_path):
                self.load_from_file(config_path)
            else:
                print(f"⚠️ Config file {config_path} not found, using defaults")
    
    def load_from_file(self, config_file):
        """Load configuration from JSON file"""
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
                for key, value in config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except Exception as e:
            print(f"Failed to load config: {e}")

def main():
    print("🚀 Starting Publisher Main...")
    
    # Load configuration
    config = PublisherConfig('config/publisher.json')
    
    # Setup metrics reporter
    try:
        metrics_reporter = HTTPMetricsReporter(config.metrics_api_url)
        print("✅ Connected to Django API for metrics")
    except Exception as e:
        print(f"⚠️ Failed to connect to API, using null reporter: {e}")
        metrics_reporter = NullMetricsReporter()
    
    # Create and start publisher
    publisher = RTSPPublisher(config, metrics_reporter)
    
    try:
        publisher.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down publisher...")
    except Exception as e:
        print(f"❌ Publisher error: {e}")
    finally:
        publisher.stop()

if __name__ == "__main__":
    main()
