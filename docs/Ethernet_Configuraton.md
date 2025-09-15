# Ethernet Configuration for Raspberry Pi

## Overview

This guide documents the process of configuring ethernet connectivity on a Raspberry Pi when the primary WiFi router has network connectivity issues. The solution involves using a Windows laptop's internet sharing feature to provide network access via ethernet cable.

## Problem

- Raspberry Pi connected to home WiFi but no internet access due to router filtering rule corruption
- Need alternative connectivity method to maintain SSH access and fix router issues
- Ethernet connection to router not working due to router problems

## Solution

Configure ethernet connection through Windows laptop internet sharing with manual IP assignment using NetworkManager.

## Prerequisites

- Raspberry Pi with NetworkManager managing network connections
- Windows laptop with both WiFi and ethernet connectivity
- Ethernet cable
- SSH access to Raspberry Pi (initially via existing connection)

## Network Management System

Verify NetworkManager is active and disable conflicting services:

```bash
# Check NetworkManager status
sudo systemctl status NetworkManager

# Stop and disable systemd-networkd to prevent conflicts
sudo systemctl stop systemd-networkd
sudo systemctl disable systemd-networkd

# Remove conflicting configuration files
sudo rm -f /etc/systemd/network/*.network
```

## Windows Configuration

### Enable Internet Sharing

1. Open **Settings** → **Network & Internet**
2. Select **Mobile hotspot**
3. Configure settings:
   - **Share my Internet connection from:** WiFi connection (e.g., HODT-5G)
   - **Share over:** Ethernet
4. **Turn ON Mobile hotspot**

### Verify Ethernet Adapter Configuration

Check Windows ethernet adapter receives IP assignment:
- Expected IP: `192.168.1.1`
- Subnet mask: `255.255.255.0`
- This creates a 192.168.1.x network for sharing

## Raspberry Pi Configuration

### Configure Ethernet Interface

Use NetworkManager to create static IP configuration matching Windows subnet:

```bash
# Create new ethernet connection with static IP
sudo nmcli connection add type ethernet ifname eth0 con-name "eth0-manual" \
    ipv4.addresses 192.168.1.2/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns 8.8.8.8 \
    ipv4.method manual

# Activate the connection
sudo nmcli connection up "eth0-manual"
```

### Verify Configuration

```bash
# Check IP assignment
ip addr show eth0

# Expected output should show:
# inet 192.168.1.2/24 brd 192.168.1.255 scope global eth0

# Test connectivity to Windows laptop
ping 192.168.1.1

# Test internet access (if sharing is working)
ping 8.8.8.8
```

## SSH Access

### Connect via PuTTY

Use the assigned static IP address:
- **Host Name:** `192.168.1.2`
- **Port:** `22`
- **Connection Type:** SSH

### Test Connection

From Windows Command Prompt:
```cmd
# Test basic connectivity
ping 192.168.1.2

# Test SSH port accessibility
telnet 192.168.1.2 22
```

## Troubleshooting

### Connection Issues

```bash
# List NetworkManager connections
sudo nmcli connection show

# Check device status
sudo nmcli device status

# Restart connection if needed
sudo nmcli connection down "eth0-manual"
sudo nmcli connection up "eth0-manual"
```

### IP Assignment Problems

```bash
# Delete existing connection and recreate
sudo nmcli connection delete "eth0-manual"

# Recreate with correct parameters
sudo nmcli connection add type ethernet ifname eth0 con-name "eth0-manual" \
    ipv4.addresses 192.168.1.2/24 \
    ipv4.gateway 192.168.1.1 \
    ipv4.dns 8.8.8.8 \
    ipv4.method manual
```

## Important Notes

- This configuration provides direct ethernet access regardless of WiFi router status
- Windows internet sharing creates a separate network segment (192.168.1.x)
- NetworkManager handles the ethernet interface exclusively
- Connection persists across reboots once properly configured
- SSH access via `192.168.1.2` bypasses router connectivity issues

## Network Architecture

```
[Windows Laptop] 192.168.1.1
       |
   [Ethernet Cable]
       |
[Raspberry Pi] 192.168.1.2
```

This configuration provides a reliable backup connection method when primary network infrastructure experiences issues.