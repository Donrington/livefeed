# WebSocket Setup Documentation

## Why Django `runserver` doesn't work with WebSockets

### The Problem
When trying to use `python manage.py runserver` with Django Channels WebSocket consumers, you will encounter errors like:
- `TimeoutError: timed out during opening handshake`
- `websockets.exceptions.InvalidStatus: server rejected WebSocket connection: HTTP 200`

### Root Cause
Django's `runserver` command uses a **WSGI (Web Server Gateway Interface)** server, which was designed only for traditional HTTP request/response cycles. WebSocket connections require:

1. **HTTP Upgrade handshake** - Client requests to upgrade from HTTP to WebSocket protocol
2. **Persistent bidirectional connection** - Unlike HTTP's request/response pattern
3. **ASGI (Asynchronous Server Gateway Interface)** support - For handling async operations

### Technical Details
- **WSGI servers** (like `runserver`) treat WebSocket upgrade requests as regular HTTP requests
- They return `HTTP 200` instead of upgrading to WebSocket protocol
- This causes the WebSocket client to timeout waiting for the protocol upgrade

### Solution: Use Daphne (ASGI Server)
Daphne is the official ASGI server for Django Channels that properly handles WebSocket connections.

#### Correct Command:
```bash
cd live_feed
daphne -b 0.0.0.0 -p 8000 live_feed.asgi:application
```

#### What Daphne Does Differently:
1. **Recognizes WebSocket upgrade requests** and responds with `HTTP 101 Switching Protocols`
2. **Maintains persistent connections** for real-time communication
3. **Handles both HTTP and WebSocket** protocols through Django's ASGI configuration

### Server Comparison
| Server Type | Protocol | WebSocket Support | Use Case |
|-------------|----------|-------------------|----------|
| `runserver` (WSGI) | HTTP only | ❌ No | Development HTTP APIs |
| `daphne` (ASGI) | HTTP + WebSocket | ✅ Yes | Real-time applications |
| `uvicorn` (ASGI) | HTTP + WebSocket | ✅ Yes | Alternative ASGI server |

### Project Configuration
Our Django project is configured for WebSocket support with:
- **Django Channels** installed
- **ASGI application** in `live_feed/asgi.py`
- **WebSocket routing** in `app/routing.py`
- **WebSocket consumer** in `app/consumers.py`

### Connection Details
- **Server**: Windows machine at `10.9.0.1:8000`
- **WebSocket URL**: `ws://10.9.0.1:8000/ws/camera/`
- **Protocol**: Sends protobuf `CameraSettings` message on connection

## Django Channels and Camera Settings Integration

### Django runserver vs ASGI Servers for WebSocket Chat Systems

**Key Point: Django's `runserver` CANNOT handle WebSocket connections, even with Django Channels configured.**

Even when you have:
- Django Channels installed (`'channels'` in `INSTALLED_APPS`)
- ASGI application configured (`ASGI_APPLICATION = 'live_feed.asgi.application'`)
- WebSocket consumers and routing set up

The `python manage.py runserver` command still uses a WSGI server internally, which only supports HTTP protocol, not WebSocket upgrades.

### Camera Settings Integration with ASGI Servers

When integrating camera settings controls (bitrate, contrast, resolution) into your template, you have these deployment options:

#### Option 1: Single ASGI Server (Recommended)
```bash
daphne -b 0.0.0.0 -p 8000 live_feed.asgi:application
```

**Advantages:**
- Handles both HTTP requests (form submissions) AND WebSocket connections
- Single port, simplified deployment
- Production-ready approach
- No CORS or cross-port communication issues

**Use Case:** Perfect for camera settings forms + real-time video streaming

#### Option 2: Dual Server Setup (Development Only)
```bash
# Terminal 1: HTTP server for forms/settings
python manage.py runserver 8000

# Terminal 2: WebSocket server for real-time features
daphne -p 8001 live_feed.asgi:application
```

**Configuration Required:**
- Frontend must connect to different ports for different features
- Camera settings forms → `http://localhost:8000`
- WebSocket video stream → `ws://localhost:8001/ws/camera/`

**Disadvantages:**
- Complex frontend configuration
- Two processes to manage
- Not suitable for production

### Production Recommendation

**Use only an ASGI server (Daphne/Uvicorn) in production.** ASGI servers efficiently handle:
- HTTP requests (including POST forms for camera settings)
- WebSocket connections (for real-time video streaming)
- Static file serving (when configured)

### Alternative ASGI Servers
```bash
# Uvicorn (alternative to Daphne)
uvicorn live_feed.asgi:application --host 0.0.0.0 --port 8000

# Hypercorn (another option)
hypercorn live_feed.asgi:application --bind 0.0.0.0:8000
```

### Conclusion
For WebSocket functionality with Django Channels, always use an ASGI server like Daphne. The traditional `runserver` command is insufficient for WebSocket protocol handling. For camera settings integration, a single ASGI server handles both HTTP forms and WebSocket streams efficiently.

