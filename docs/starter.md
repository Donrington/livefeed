
# Live Feed Application Starter Guide

## Requirements
- Python 3.13.7

## Running the Application

### Start the Django Application
Start the Django application using Daphne:
```bash
cd live_feed
daphne -b 0.0.0.0 -p 9000 live_feed.asgi:application
```

### Start the Publisher
To start the publisher, you need to:
1. Download MediaMTX from https://github.com/bluenviron/mediamtx
2. Run the publisher with the MediaMTX path:
```bash
python3 zero_latency_publisher.py --mediamtx-path /path/to/mediamtx
```

**Example:**
```bash
python3 zero_latency_publisher.py --mediamtx-path /home/user/Desktop/mediamtx
```