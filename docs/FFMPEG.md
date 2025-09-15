# FFmpeg Windows Installation Guide

## Quick Setup (5 minutes)

### 1. Download FFmpeg
- Go to **https://www.gyan.dev/ffmpeg/builds/**
- Download: `ffmpeg-release-essentials.zip` (latest version)
- File size: ~70MB

### 2. Extract Files
```
C:\ffmpeg\
├── bin\
│   ├── ffmpeg.exe
│   ├── ffplay.exe
│   └── ffprobe.exe
├── doc\
└── presets\
```

### 3. Add to PATH Environment Variable

#### Method 1: GUI (Recommended)
1. **Open System Properties**
   - Press `Win + X` → Select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables..."

2. **Edit PATH Variable**
   - Under "System variables" → Find and select "Path"
   - Click "Edit..." → Click "New"
   - Add: `C:\ffmpeg\bin`
   - Click "OK" on all dialogs

#### Method 2: Command Line (PowerShell as Admin)
```powershell
# Add FFmpeg to PATH permanently
$env:Path += ";C:\ffmpeg\bin"
[Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::Machine)
```

### 4. Verify Installation
Open **new** Command Prompt or PowerShell:
```cmd
ffmpeg -version
```

Expected output:
```
ffmpeg version 6.x.x Copyright (c) 2000-2024 the FFmpeg developers
built with gcc 13.2.0 (Rev5, Built by MSYS2 project)
configuration: --enable-gpl --enable-version3...
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `'ffmpeg' is not recognized` | Restart terminal after adding to PATH |
| Permission denied | Run PowerShell as Administrator |
| PATH not working | Check spelling: `C:\ffmpeg\bin` (not `C:\ffmpeg\`) |
| Still not working | Reboot computer to refresh environment |

## Quick Test
```cmd
# Test basic functionality
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 test.mp4
```

## Alternative: Chocolatey (One-liner)
```powershell
# Install Chocolatey first, then:
choco install ffmpeg
```

---
**Note**: Close and reopen any terminal/IDE after installation to refresh PATH variables.