# OpenVPN Setup Journey - Raspberry Pi to Windows

## Project Overview
Successfully implemented secure VPN connection between Raspberry Pi (server) and Windows machine (client) to enable encrypted remote access to surveillance system.

## Setup Process

### 1. Raspberry Pi OpenVPN Server Installation
- Installed OpenVPN server on Raspberry Pi
- Created client certificate for "nextgen25" 
- Generated client configuration file: `/home/nextgen/nextgen25.ovpn`

### 2. Initial Issue Encountered
**Problem**: Client configuration contained wrong IP address
- Generated .ovpn file had external IP: `102.89.43.27:1194`
- Should have been local IP: `192.168.0.183:1194`

**Windows Error Log**:
```
TLS Error: TLS key negotiation failed to occur within 60 seconds
UDP link remote: [AF_INET]102.89.43.27:1194
```

### 3. Resolution Steps
**Issue**: Permission denied when editing .ovpn file
```bash
Error writing /home/nextgen/nextgen25.ovpn: Permission denied
```

**Solution**: Used sudo to edit configuration
```bash
sudo sed -i 's/102.89.43.27/192.168.0.183/g' /home/nextgen/nextgen25.ovpn
```

### 4. Windows Client Setup
- Installed OpenVPN GUI on Windows
- Imported corrected `nextgen25.ovpn` configuration
- Established successful VPN connection

## Network Configuration

### VPN Network Details
- **Server IP (VPN)**: 10.8.0.1 (Raspberry Pi)
- **Client IP Pool**: 10.8.0.2 - 10.8.0.254
- **Protocol**: UDP Port 1194
- **Encryption**: TLS/SSL tunnel

### Access Methods
- **Local Network**: `rtsp://192.168.0.183:8554/zerolatency`
- **VPN Access**: `rtsp://10.8.0.1:8554/zerolatency`
- **Web Browser**: `http://10.8.0.1:8888/zerolatency/index.m3u8`

## Success Verification
Connection established successfully with excellent performance:
```
Ping statistics for 10.8.0.1:
Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
Approximate round trip times: Minimum = 5ms, Maximum = 6ms, Average = 5ms
```

## Benefits Achieved
✅ **Encrypted tunnel** between Windows and Raspberry Pi  
✅ **Secure remote access** to surveillance system  
✅ **Low latency connection** (5-6ms)  
✅ **Private network** for device communication  

---

# OpenVPN Commands Reference

## Raspberry Pi (Linux Server)





### Server Management
```bash
# Check OpenVPN server status
sudo systemctl status openvpn@server

# Start/Stop/Restart OpenVPN server
sudo systemctl start openvpn@server
sudo systemctl stop openvpn@server
sudo systemctl restart openvpn@server

# Enable auto-start on boot
sudo systemctl enable openvpn@server

# View real-time logs
sudo journalctl -u openvpn@server -f

# Check connected clients
sudo cat /var/log/openvpn/status.log

# Check listening ports
sudo netstat -tulpn | grep 1194
```

### Client Certificate Management
```bash
# Add new client
sudo /usr/local/bin/openvpn-install.sh

# View client configuration
sudo cat /home/username/clientname.ovpn

# Fix client configuration IP
sudo sed -i 's/OLD_IP/NEW_IP/g' /home/username/clientname.ovpn

# Check client file permissions
ls -la /home/username/*.ovpn
sudo chown username:username /home/username/clientname.ovpn
```

### Firewall Configuration
```bash
# Allow OpenVPN port
sudo ufw allow 1194/udp

# Allow VPN subnet
sudo ufw allow from 10.8.0.0/24

# Check firewall status
sudo ufw status
```

### Network Diagnostics
```bash
# Check OpenVPN interface
ip addr show tun0

# Monitor VPN traffic
sudo tcpdump -i tun0

# Check routing table
ip route show
```






## Windows Client

### Connection Management
```cmd
# Manual connection (Run as Administrator)
cd "C:\Program Files\OpenVPN\bin"
openvpn.exe --config "C:\path\to\client.ovpn"

# Check VPN adapter status
ipconfig | findstr "OpenVPN"

# View all network adapters
ipconfig /all
```

### Testing VPN Connection
```cmd
# Test VPN server connectivity
ping 10.8.0.1

# Test route to VPN server
tracert 10.8.0.1

# Test SSH via VPN
ssh username@10.8.0.1

# Test surveillance stream via VPN
# Use in VLC: rtsp://10.8.0.1:8554/streamname
```

### Network Diagnostics
```cmd
# Check routing table
route print

# Check active connections
netstat -an | findstr 1194

# Test basic connectivity to server
ping 192.168.0.183
telnet 192.168.0.183 1194
```

### Firewall Management
```cmd
# Check Windows Firewall (Run as Administrator)
netsh advfirewall show allprofiles

# Temporarily disable firewall for testing
netsh advfirewall set allprofiles state off

# Re-enable firewall
netsh advfirewall set allprofiles state on
```




## GUI Applications

### Windows OpenVPN GUI
- **Install**: Download from https://openvpn.net/community-downloads/
- **Config Location**: `C:\Program Files\OpenVPN\config\`
- **Connect**: Right-click system tray icon → Connect
- **View Logs**: Right-click system tray icon → View Log

### OpenVPN Connect (Alternative)
- **Install**: Download OpenVPN Connect app
- **Import**: Click "+" → Import Profile → Select .ovpn file
- **Connect**: Click connect button in app interface

## Quick Verification Commands

### Raspberry Pi
```bash
# One-liner server check
sudo systemctl is-active openvpn@server && echo "Server Running" || echo "Server Stopped"

# Quick client list
sudo grep "CLIENT LIST" -A 10 /var/log/openvpn/status.log
```

### Windows
```cmd
# Quick VPN status check
ping 10.8.0.1 && echo "VPN Connected" || echo "VPN Disconnected"

# Show VPN IP
ipconfig | findstr "10.8.0"
```

## Troubleshooting Quick Reference

| Issue | Linux Command | Windows Command |
|-------|---------------|-----------------|
| Server not running | `sudo systemctl restart openvpn@server` | - |
| Can't connect | `sudo journalctl -u openvpn@server -f` | Check OpenVPN GUI logs |
| Wrong IP in config | `sudo nano /path/to/client.ovpn` | Edit .ovpn file |
| Firewall blocking | `sudo ufw allow 1194/udp` | Disable Windows Firewall temporarily |
| Check connection | `sudo cat /var/log/openvpn/status.log` | `ping 10.8.0.1` |

---

**Note**: Always run OpenVPN commands with appropriate privileges (sudo on Linux, Administrator on Windows) and ensure firewall rules allow VPN traffic.


**Error Encounter**: encountered a firewall blocking inbound and outbound traffic causing a ping issue from the pi to the windows so i had to add a specific rule to allow inbound ICMP (ping traffic) so i can have full bidirectional connectivity through my openvpn tunnel

# Allow SSH from VPN subnet
netsh advfirewall firewall add rule name="VPN SSH In" dir=in action=allow protocol=tcp localport=22 remoteip=10.8.0.0/24

# Allow RDP if you need remote desktop access
netsh advfirewall firewall add rule name="VPN RDP In" dir=in action=allow protocol=tcp localport=3389 remoteip=10.8.0.0/24
