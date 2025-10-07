/* ============================================================================
   DASHBOARD JAVASCRIPT
   ============================================================================ */

let cameraWebSocket = null;
let isConnected = false;
let isRecording = false;
let currentView = 'all';

// === FPS COUNTER (Real-time message rate tracking) ===
function createFpsCounter(windowMs = 1000) {
    const ts = [];

    function prune(now) {
        while (ts.length && now - ts[0] > windowMs) ts.shift();
    }

    return {
        tick(now = performance.now()) {
            ts.push(now);
            prune(now);
        },

        fps(now = performance.now()) {
            prune(now);
            return ts.length * 1000 / windowMs;
        },
    };
}

const fpsCounter = createFpsCounter(1000);

// Camera selection
function selectCamera(cameraId) {
    currentView = cameraId;

    // Update button states
    document.querySelectorAll('[id^="btn-camera-"]').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`btn-camera-${cameraId}`).classList.add('active');

    // Show/hide appropriate view
    if (cameraId === 'all') {
        document.getElementById('camera-grid-all').classList.remove('hidden');
        document.getElementById('camera-grid-single').classList.add('hidden');
    } else {
        document.getElementById('camera-grid-all').classList.add('hidden');
        document.getElementById('camera-grid-single').classList.remove('hidden');
        document.getElementById('single-camera-label').textContent = `Camera ${cameraId}`;
    }
}

// Section switching
function showSection(section) {
    if (section === 'cameras') {
        document.getElementById('cameras-section').classList.remove('hidden');
        document.getElementById('recordings-section').classList.add('hidden');
    } else if (section === 'recordings') {
        document.getElementById('cameras-section').classList.add('hidden');
        document.getElementById('recordings-section').classList.remove('hidden');
    }
}

// Recording playback
function playRecording(filename, title) {
    const player = document.getElementById('recording-player');
    player.src = `/media/recordings/${filename}`;
    player.load();
    player.play();
    console.log('Playing recording:', title);
}

// Recording control
function toggleRecording() {
    isRecording = !isRecording;
    const recordBtn = document.getElementById('record-btn');
    const recordingStatus = document.getElementById('recording-status');

    if (isRecording) {
        recordBtn.innerHTML = '<i class="fas fa-stop mr-2"></i>Stop Recording';
        recordBtn.classList.add('bg-red-600');
        recordingStatus.textContent = 'Recording...';
    } else {
        recordBtn.innerHTML = '<i class="fas fa-record-vinyl mr-2 text-red-500"></i>Start Recording';
        recordBtn.classList.remove('bg-red-600');
        recordingStatus.textContent = 'Ready to record';
    }
}

// Connect individual camera
async function connectCamera(cameraId, event) {
    console.log(`🔌 Connecting to Camera ${cameraId}...`);

    // Add ripple effect to button
    const button = event.currentTarget.querySelector('.connect-btn-overlay');
    button.classList.add('clicked');
    setTimeout(() => button.classList.remove('clicked'), 600);

    try {
        // Fetch stream configuration from API
        const response = await fetch('/api/status/');
        const config = await response.json();

        console.log('Stream config:', config);

        // Get video element
        const video = document.getElementById(`video-${cameraId}`);

        // Connect using WebRTC (preferred for low latency)
        if (config.webrtc_url) {
            await connectVideoWebRTC(video, config.webrtc_url, cameraId);
        } else {
            throw new Error('No stream URL available');
        }

        // Hide overlay and show video on success
        const overlay = document.getElementById(`overlay-${cameraId}`);
        setTimeout(() => {
            overlay.classList.add('hidden');
            video.classList.remove('hidden');
        }, 300);

        console.log(`✅ Camera ${cameraId} connected successfully`);
    } catch (error) {
        console.error(`❌ Failed to connect Camera ${cameraId}:`, error);
        alert(`Failed to connect to camera: ${error.message}`);
    }
}

// WebRTC connection for video element
async function connectVideoWebRTC(videoElement, webrtcUrl, cameraId) {
    console.log(`📡 Connecting Camera ${cameraId} via WebRTC...`);

    const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    pc.ontrack = (event) => {
        console.log(`✅ Camera ${cameraId} stream received`);
        videoElement.srcObject = event.streams[0];
        videoElement.play().catch(e => console.error('Play error:', e));
    };

    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const response = await fetch(webrtcUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: offer.sdp
    });

    if (!response.ok) {
        throw new Error(`WebRTC connection failed: ${response.statusText}`);
    }

    const answer = await response.text();
    await pc.setRemoteDescription({
        type: 'answer',
        sdp: answer
    });

    return pc;
}

// Connect single camera view
async function connectSingleCamera(event) {
    console.log('🔌 Connecting to single camera view...');

    // Add ripple effect to button
    const button = event.currentTarget.querySelector('.connect-btn-overlay');
    button.classList.add('clicked');
    setTimeout(() => button.classList.remove('clicked'), 600);

    try {
        // Fetch stream configuration from API
        const response = await fetch('/api/status/');
        const config = await response.json();

        console.log('Stream config:', config);

        // Get video element
        const video = document.getElementById('video-single');

        // Connect using WebRTC (preferred for low latency)
        if (config.webrtc_url) {
            await connectVideoWebRTC(video, config.webrtc_url, 'single');
        } else {
            throw new Error('No stream URL available');
        }

        // Hide overlay and show video on success
        const overlay = document.getElementById('overlay-single');
        setTimeout(() => {
            overlay.classList.add('hidden');
            video.classList.remove('hidden');
        }, 300);

        console.log('✅ Single camera connected successfully');
    } catch (error) {
        console.error('❌ Failed to connect single camera:', error);
        alert(`Failed to connect to camera: ${error.message}`);
    }
}

// Connect to camera system
function handleConnect() {
    console.log('🔌 Connecting to camera system...');

    const wsUrl = `ws://${window.location.host}/ws/camera/`;
    cameraWebSocket = new WebSocket(wsUrl);

    cameraWebSocket.onopen = function() {
        console.log('✅ Connected to camera system');
        showConnectedState();
    };

    cameraWebSocket.onmessage = function(event) {
        try {
            const message = JSON.parse(event.data);
            handleCameraMessage(message);
        } catch (e) {
            console.error('❌ Error parsing message from Pi:', e, 'Raw message:', event.data);
        }
    };

    cameraWebSocket.onclose = function() {
        console.log('❌ Disconnected from camera system');
        showDisconnectedState();
    };
}

// Stop/Disconnect from camera system
function handleStop() {
    console.log('⏹️ Stopping camera system...');

    if (cameraWebSocket) {
        cameraWebSocket.close();
        cameraWebSocket = null;
    }

    // Reset all camera feeds
    for (let i = 1; i <= 4; i++) {
        const overlay = document.getElementById(`overlay-${i}`);
        overlay.classList.remove('hidden');

        const video = document.getElementById(`video-${i}`);
        video.classList.add('hidden');
        video.src = '';
    }

    // Reset single camera view
    const overlaySingle = document.getElementById('overlay-single');
    overlaySingle.classList.remove('hidden');

    const videoSingle = document.getElementById('video-single');
    videoSingle.classList.add('hidden');
    videoSingle.src = '';

    showDisconnectedState();
    console.log('✅ Camera system stopped');
}

// === Enhanced message handler with type-based routing ===
function handleCameraMessage(message) {
    switch(message.type) {
        case 'connection_status':
            handleConnectionStatus(message);
            break;

        case 'camera_settings_update':
            handleCameraSettings(message);
            break;

        case 'system_metrics':
            handleSystemMetrics(message);
            break;

        case 'error_alert':
            handleErrorAlert(message);
            break;

        default:
            console.warn('⚠️ Unknown message type:', message.type, message);
    }
}

// === Handle connection status messages ===
function handleConnectionStatus(message) {
    if (typeof message.isConnected !== 'undefined') {
        fpsCounter.tick();

        const currentFps = fpsCounter.fps();
        document.getElementById('fps-display').textContent = currentFps.toFixed(1);

        if (message.isConnected) {
            document.getElementById('health-value').textContent = '100';
        } else {
            console.warn('⚠️ Camera feed interrupted!');
            document.getElementById('health-value').textContent = '50';
        }
    }
}

// Handle camera settings updates
function handleCameraSettings(message) {
    const brightnessSlider = document.getElementById('camera-brightness-slider');
    const brightnessValue = document.getElementById('camera-brightness-value');

    if (brightnessSlider && message.brightness) {
        brightnessSlider.value = message.brightness;
        if (brightnessValue) {
            brightnessValue.textContent = message.brightness;
        }
    }
}

// === Handle system metrics ===
function handleSystemMetrics(message) {
    if (message.cpu !== undefined) {
        document.getElementById('cpu-usage').textContent = Math.round(message.cpu);
        document.getElementById('cpu-bar').style.width = `${message.cpu}%`;
    }

    if (message.memory !== undefined) {
        document.getElementById('memory-usage').textContent = Math.round(message.memory);
        if (message.memory_used_mb && message.memory_total_mb) {
            document.getElementById('memory-used').textContent = message.memory_used_mb;
            document.getElementById('memory-total').textContent = message.memory_total_mb;
        }
    }

    if (message.network_mbps !== undefined) {
        document.getElementById('network-upload').textContent = `${message.network_mbps.toFixed(2)} Mbps`;
    }

    if (message.latency_ms !== undefined) {
        document.getElementById('network-latency').textContent = `${message.latency_ms} ms`;
    }

    if (message.fps !== undefined) {
        document.getElementById('fps-display').textContent = message.fps.toFixed(1);
    }
}

// === Handle error alerts ===
function handleErrorAlert(message) {
    console.error('🚨 System alert:', message.message);
    alert(`System Alert: ${message.message}`);
}

function showConnectedState() {
    isConnected = true;
    document.getElementById('status-badge').className = 'badge live';
    document.getElementById('status-badge').innerHTML = '<div class="h-1.5 w-1.5 rounded-full bg-green-500"></div>CONNECTED';
    document.getElementById('status-text').textContent = 'CONNECTED';

    const connectBtn = document.getElementById('connect-btn');
    connectBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Connected';
    connectBtn.disabled = true;
    connectBtn.classList.add('opacity-50', 'cursor-not-allowed');

    const stopBtn = document.getElementById('stop-btn');
    stopBtn.disabled = false;

    document.getElementById('record-btn').disabled = false;

    document.getElementById('connection-percent').textContent = '100';
    document.getElementById('connection-bar').style.width = '100%';
    document.getElementById('connection-bar').style.background = 'linear-gradient(to right, #10b981, #059669)';

    document.getElementById('quality-percent').textContent = '95';
    document.getElementById('quality-bar').style.width = '95%';

    document.getElementById('health-value').textContent = '100';

    console.log('✅ Connected - waiting for real-time data from Pi...');
}

function showDisconnectedState() {
    isConnected = false;
    document.getElementById('status-badge').className = 'badge offline';
    document.getElementById('status-badge').innerHTML = '<div class="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse"></div>NOT CONNECTED';
    document.getElementById('status-text').textContent = 'NOT CONNECTED';

    const connectBtn = document.getElementById('connect-btn');
    connectBtn.innerHTML = '<i class="fas fa-plug mr-2"></i>Connect';
    connectBtn.disabled = false;
    connectBtn.classList.remove('opacity-50', 'cursor-not-allowed');

    const stopBtn = document.getElementById('stop-btn');
    stopBtn.disabled = true;

    document.getElementById('record-btn').disabled = true;

    document.getElementById('connection-percent').textContent = '0';
    document.getElementById('connection-bar').style.width = '0%';
    document.getElementById('quality-percent').textContent = '0';
    document.getElementById('quality-bar').style.width = '0%';
    document.getElementById('health-value').textContent = '0';
    document.getElementById('fps-display').textContent = '0';
    document.getElementById('cpu-usage').textContent = '0';
    document.getElementById('cpu-bar').style.width = '0%';
    document.getElementById('memory-usage').textContent = '0';
}

// Send camera settings
function sendCameraSetting(setting, value) {
    if (cameraWebSocket && cameraWebSocket.readyState === WebSocket.OPEN) {
        const message = {
            type: 'update_camera_settings',
            setting: setting,
            value: value
        };
        cameraWebSocket.send(JSON.stringify(message));
        console.log(`📡 Sent ${setting}: ${value}`);
    }
}

// Toggle metrics section
let metricsVisible = true;
function toggleMetrics() {
    metricsVisible = !metricsVisible;
    const metricsContent = document.getElementById('metrics-content');
    const toggleIcon = document.getElementById('metrics-toggle-icon');

    if (metricsVisible) {
        metricsContent.classList.remove('collapsed');
        toggleIcon.className = 'fas fa-chevron-up';
    } else {
        metricsContent.classList.add('collapsed');
        toggleIcon.className = 'fas fa-chevron-down';
    }
}

// Initialize dashboard
function initDashboard() {
    console.log('🚀 Security Surveillance Dashboard Starting...');
    console.log('✅ Dashboard Ready');
}

// Start the application
document.addEventListener('DOMContentLoaded', initDashboard);
