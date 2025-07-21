#!/usr/bin/env python3
import sys
import os

# Since this file is in ROOT directory, we need to add ROOT to path
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)  # receiver/ folder
parent_dir = os.path.dirname(current_dir)    # root/ folder (where shared/ is)

# Add the PARENT directory to Python path
sys.path.insert(0, parent_dir)
print(f"📁 Current dir: {current_dir}")
print(f"📁 Parent dir: {parent_dir}")

try:
    from shared.base import HTTPMetricsReporter, NullMetricsReporter
    print("✅ Successfully imported from shared.base")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

from receiver.main import HLSReceiver

class ReceiverConfig:
    def __init__(self, config_file=None):
        self.hls_url = 'http://localhost:8888/mystream/index.m3u8'
        self.metrics_api_url = 'http://localhost:8000/api/metrics/receiver/'

def main():
    print("🚀 Starting Receiver...")
    
    config = ReceiverConfig()
    
    try:
        metrics_reporter = HTTPMetricsReporter(config.metrics_api_url)
        print("✅ Connected to Django API")
    except:
        metrics_reporter = NullMetricsReporter()
        print("⚠️ Using null metrics reporter")
    
    receiver = HLSReceiver(config, metrics_reporter)
    
    try:
        receiver.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down receiver...")
    except Exception as e:
        print(f"❌ Receiver error: {e}")
    finally:
        receiver.stop()

if __name__ == "__main__":
    main()