# OpenCV 4.13.0 Installation Journey - Raspberry Pi 4

## Project Overview
**Objective**: Install OpenCV 4.13.0 from source on Raspberry Pi 4 Model B (4GB RAM) running Raspberry Pi OS  
**Date**: August 2025  
**Platform**: ARM64 architecture, Debian-based system  

## Initial Setup and Prerequisites

### System Configuration
- **Hardware**: Raspberry Pi 4 Model B, 4GB RAM
- **OS**: Raspberry Pi OS (Debian-based)
- **Architecture**: ARM64
- **Available Storage**: 117GB (6% used initially)

### SSH Connection Issue (Pre-Installation)
**Problem**: SSH connection refused error when attempting remote access
```
ssh: connect to host raspberrypi port 22: Connection refused
```

**Root Cause**: SSH service was not enabled by default on the Raspberry Pi OS image

**Resolution**: 
1. Created an empty file named `ssh` (no extension) in the boot partition of the SD card
2. This automatically enabled SSH on first boot
3. Successfully connected via `ssh nextgen@192.168.0.183`

## OpenCV Build Process and Challenges

### Initial Build Configuration
Used a comprehensive build script targeting OpenCV 4.13.0 with opencv_contrib modules, including dependencies for:
- Video processing (FFmpeg, GStreamer)
- Image formats (JPEG, TIFF, PNG)
- Threading optimization (TBB, OpenMP)
- Hardware acceleration (NEON, VFPV3)

### Critical Issue #1: TBB Atomic Operations Linker Errors

**Error Encountered**:
```
/usr/bin/ld: undefined reference to '__atomic_fetch_sub_8'
/usr/bin/ld: undefined reference to '__atomic_fetch_add_8'
/usr/bin/ld: undefined reference to '__atomic_load_8'
collect2: error: ld returned 1 exit status
make[2]: *** [lib/libtbb.so] Error 1
```

**Technical Analysis**:
- Error occurred during TBB (Threading Building Blocks) library compilation
- TBB version 2022.1.0 included with OpenCV 4.13.0 has compatibility issues with ARM architecture
- The linker couldn't resolve 64-bit atomic operations required by TBB on ARM systems
- This is a known issue with newer TBB versions on ARM platforms

**Troubleshooting Process**:
1. **Initial Assessment**: Confirmed RAM usage was not the bottleneck (4GB available, usage remained low)
2. **Build Log Analysis**: Used verbose compilation to identify the exact failure point
3. **Error Pattern Recognition**: Identified atomic operation undefined references as TBB-specific issue

**Resolution Strategy**:
Modified CMake configuration to disable TBB completely:
```cmake
-D WITH_TBB=OFF \
-D BUILD_TBB=OFF \
```

**Alternative Solutions Considered**:
1. Using system TBB package instead of building from source
2. Adding explicit atomic library linking (`-latomic` flags)
3. Using different TBB version or patches

**Final Working Configuration**:
```bash
cmake -D CMAKE_BUILD_TYPE=RELEASE \
-D CMAKE_INSTALL_PREFIX=/usr/local \
-D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
-D ENABLE_NEON=ON \
-D ENABLE_VFPV3=ON \
-D WITH_OPENMP=ON \
-D WITH_OPENCL=OFF \
-D BUILD_TIFF=ON \
-D WITH_FFMPEG=ON \
-D WITH_TBB=OFF \
-D BUILD_TBB=OFF \
-D WITH_GSTREAMER=ON \
-D BUILD_TESTS=OFF \
-D WITH_EIGEN=OFF \
-D WITH_V4L=ON \
-D WITH_LIBV4L=ON \
-D WITH_VTK=OFF \
-D WITH_QT=OFF \
-D WITH_PROTOBUF=ON \
-D OPENCV_ENABLE_NONFREE=ON \
-D INSTALL_C_EXAMPLES=OFF \
-D INSTALL_PYTHON_EXAMPLES=OFF \
-D PYTHON3_PACKAGES_PATH=/usr/lib/python3/dist-packages \
-D OPENCV_GENERATE_PKGCONFIG=ON \
-D BUILD_EXAMPLES=OFF ..
```

## Performance Optimizations Applied

### ARM-Specific Optimizations
- **NEON SIMD**: Enabled ARM NEON SIMD instructions for vectorized operations
- **VFPV3**: Enabled Vector Floating Point v3 for enhanced floating-point performance
- **OpenMP**: Maintained OpenMP for CPU-level parallelization

### Compilation Strategy
- **Threading**: Used `make -j2` (2 parallel jobs) to balance compilation speed with system stability
- **Memory Management**: Monitored system resources during compilation to prevent memory exhaustion

## Post-Installation Issues

### PKG-Config Path Configuration
**Problem**: `pkg-config --modversion opencv4` returned "Package not found"

**Root Cause**: OpenCV installation path not included in PKG_CONFIG_PATH environment variable

**Resolution**:
```bash
export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig
echo 'export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig' >> ~/.bashrc
sudo ldconfig
```

## Technical Impact and Trade-offs

### Performance Implications
**Loss**: Disabling TBB removes some multi-threaded optimization capabilities
**Mitigation**: OpenMP still provides CPU-level parallelization for most operations
**Real-world Impact**: Minimal performance difference for typical computer vision applications

### Successful Installation Verification
```python
import cv2
print(cv2.__version__)  # Output: 4.13.0
```

### Functional Testing
- Basic image processing operations confirmed working
- Camera interface accessible via `cv2.VideoCapture(0)`
- All core OpenCV modules available

## Key Lessons Learned

1. **ARM Compatibility**: TBB 2022.1.0 has known issues with ARM architectures, particularly in 32-bit mode
2. **Verbose Debugging**: Using `make VERBOSE=1` is crucial for identifying specific compilation failures
3. **Incremental Problem Solving**: Systematic elimination of build components helps isolate issues
4. **Environment Setup**: Post-installation environment variable configuration is critical for development workflow

## Alternative Approaches for Future Reference

### Pre-compiled Options
```bash
# Faster installation for development use
sudo apt install python3-opencv
pip3 install opencv-python opencv-contrib-python
```

### System TBB Integration
```bash
# Use system TBB instead of building from source
sudo apt install libtbb-dev
cmake ... -D WITH_TBB=ON -D BUILD_TBB=OFF ...
```

## Conclusion

Successfully installed OpenCV 4.13.0 from source on Raspberry Pi 4 by identifying and resolving TBB atomic operations compatibility issues. The solution involved disabling problematic TBB compilation while maintaining other performance optimizations. Total installation time: ~4 hours including troubleshooting.

**Final Status**: Fully functional OpenCV 4.13.0 installation with Python bindings, ready for computer vision development projects.