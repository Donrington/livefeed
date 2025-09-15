# Live Feed Project Documentation

This folder contains all documentation for the Live Feed streaming system with VPN setup between Windows and Raspberry Pi.

## 📋 Documentation Index

### Core Project Documentation
- **[CLAUDE.md](./CLAUDE.md)** - Main project instructions and codebase guidelines for Claude AI assistant
- **[README.md](./README.md)** - Original project README with overview and setup instructions

### System Setup & Configuration
- **[VPN_SETUP_BRIEFING.md](./VPN_SETUP_BRIEFING.md)** - Complete VPN setup between Windows and Raspberry Pi
- **[testvpn_setup_pi-windows.txt](./testvpn_setup_pi-windows.txt)** - VPN configuration testing notes
- **[Ethernet_Configuraton.md](./Ethernet_Configuraton.md)** - Network and ethernet configuration details
- **[requirements.txt](./requirements.txt)** - Python dependencies for the project

### Journey & Learning Documentation  
- **[RaspberryPi_Journey.md](./RaspberryPi_Journey.md)** - Step-by-step Raspberry Pi setup and configuration
- **[Openvpn_journey.md](./Openvpn_journey.md)** - OpenVPN setup process and troubleshooting
- **[OpenCv_Journey.md](./OpenCv_Journey.md)** - OpenCV installation and setup process

### Technical Implementation
- **[NETWORK_CONFIG_REFACTOR.md](./NETWORK_CONFIG_REFACTOR.md)** - Recent code refactoring for centralized network configuration
- **[FFMPEG.md](./FFMPEG.md)** - FFMPEG setup and streaming configuration
- **[openvpn.txt](./openvpn.txt)** - OpenVPN configuration notes
- **[staticmethod.txt](./staticmethod.txt)** - Python static method implementation notes

## 🎯 Quick Start Guide

1. **System Setup**: Start with [VPN_SETUP_BRIEFING.md](./VPN_SETUP_BRIEFING.md) for network configuration
2. **Pi Configuration**: Follow [RaspberryPi_Journey.md](./RaspberryPi_Journey.md) for device setup  
3. **Code Structure**: Check [NETWORK_CONFIG_REFACTOR.md](./NETWORK_CONFIG_REFACTOR.md) for recent improvements
4. **Development**: See [CLAUDE.md](./CLAUDE.md) for coding guidelines and project structure

## 🔧 System Architecture

```
Windows Machine (10.9.0.1)          Raspberry Pi (10.9.0.2)
├── Django Web App (Port 8080)       ├── MediaMTX Server
├── Zero Latency Receiver             │   ├── RTSP: 8554
└── VPN Client                        │   ├── HLS: 8888
                                      │   └── WebRTC: 8889
                                      ├── Zero Latency Publisher
                                      └── VPN Server
```

## 📁 Project Structure
```
livefeed/
├── docs/                    # 📚 All documentation (you are here)
├── live_feed/              # 🌐 Django web application
│   ├── app/                # 📱 Main Django app
│   │   ├── config.py       # ⚙️ Centralized network configuration
│   │   └── views.py        # 🎮 API endpoints
│   └── templates/          # 🎨 HTML templates
├── zero_latency_publisher.py  # 📹 Pi camera streaming
└── zero_latency_receiver.py   # 📺 Windows stream receiver
```

## 🚀 Recent Updates
- **Network Configuration Refactor**: Centralized IP addresses and ports in `config.py`
- **UI Improvements**: Eliminated localhost placeholders, now shows real Pi IP addresses
- **Code Organization**: All documentation moved to `/docs` folder for better structure