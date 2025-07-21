
# Create: check_mediamtx.py
import subprocess
import requests
import socket

def check_mediamtx():
    """Check if MediaMTX is running and accessible"""
    print("🔍 Checking MediaMTX status...")
    
    # Check if port 8554 is open (RTSP)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8554))
        sock.close()
        
        if result == 0:
            print("✅ MediaMTX RTSP port 8554 is open")
        else:
            print("❌ MediaMTX RTSP port 8554 is not accessible")
            print("   Please start MediaMTX first:")
            print("   ./mediamtx.exe")
            return False
    except Exception as e:
        print(f"❌ Cannot check RTSP port: {e}")
        return False
    
    # Check if MediaMTX web interface is running
    try:
        response = requests.get("http://localhost:9997", timeout=2)
        print("✅ MediaMTX web interface is accessible")
    except:
        print("⚠️ MediaMTX web interface not accessible (this is OK)")
    
    return True

def test_ffmpeg():
    """Test if FFmpeg is working"""
    print("\n🧪 Testing FFmpeg...")
    
    try:
        # Simple FFmpeg test
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is working")
            return True
        else:
            print("❌ FFmpeg failed")
            return False
    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        return False

if __name__ == "__main__":
    mediamtx_ok = check_mediamtx()
    ffmpeg_ok = test_ffmpeg()
    
    if mediamtx_ok and ffmpeg_ok:
        print("\n✅ System ready for zero latency streaming!")
    else:
        print("\n❌ Please fix the issues above before running publisher")
