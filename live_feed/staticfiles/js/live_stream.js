/* ============================================================================
   LIVE STREAM JAVASCRIPT
   ============================================================================ */

// === STATE MANAGEMENT ===
let isPlaying = false;
let isMuted = false;
let isTheaterMode = false;
let currentVolume = 100;
let streamConnection = null;
let videoElement = document.getElementById('video-player');
let loadingOverlay = document.getElementById('loading-overlay');

// === DOM ELEMENTS ===
const playPauseBtn = document.getElementById('play-pause-btn');
const volumeBtn = document.getElementById('volume-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');
const theaterBtn = document.getElementById('theater-btn');
const qualityBtn = document.getElementById('quality-btn');
const qualityMenu = document.getElementById('quality-menu');
const videoContainer = document.getElementById('video-container');
const chatInput = document.getElementById('chat-input');
const sendChatBtn = document.getElementById('send-chat-btn');

// === VIDEO CONTROLS ===

// Play/Pause
function togglePlayPause() {
    if (isPlaying) {
        videoElement.pause();
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    } else {
        videoElement.play();
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    }
    isPlaying = !isPlaying;
}

// Volume
function toggleMute() {
    if (isMuted) {
        videoElement.muted = false;
        volumeBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
        document.querySelector('.volume-fill').style.width = currentVolume + '%';
    } else {
        videoElement.muted = true;
        volumeBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
        document.querySelector('.volume-fill').style.width = '0%';
    }
    isMuted = !isMuted;
}

// === STREAM CONNECTION ===

async function connectToStream() {
    console.log('🎬 Connecting to live stream...');

    try {
        // Fetch stream configuration
        const response = await fetch('/api/status/');
        const data = await response.json();

        console.log('Stream config:', data);

        // Connect using WebRTC
        if (data.webrtc_url) {
            await connectWebRTC(data.webrtc_url);
        } else if (data.hls_url) {
            connectHLS(data.hls_url);
        } else {
            throw new Error('No stream URL available');
        }

        // Update UI
        updateLiveStatus(true);

    } catch (error) {
        console.error('Failed to connect to stream:', error);
        loadingOverlay.innerHTML = `
            <div class="text-center">
                <i class="fas fa-exclamation-circle text-red-500 text-4xl mb-4"></i>
                <p class="text-white text-lg">Connection Failed</p>
                <p class="text-slate-400 text-sm mt-2">${error.message}</p>
                <button onclick="connectToStream()" class="mt-4 btn bg-cyan-600 text-white px-6 py-2 rounded-lg">
                    Retry
                </button>
            </div>
        `;
    }
}

async function connectWebRTC(webrtcUrl) {
    console.log('📡 Connecting via WebRTC...');

    streamConnection = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    streamConnection.ontrack = (event) => {
        console.log('✅ Stream connected!');
        videoElement.srcObject = event.streams[0];
        videoElement.play();
        loadingOverlay.style.display = 'none';
        isPlaying = true;
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    };

    streamConnection.addTransceiver('video', { direction: 'recvonly' });

    const offer = await streamConnection.createOffer();
    await streamConnection.setLocalDescription(offer);

    const response = await fetch(webrtcUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: offer.sdp
    });

    const answer = await response.text();
    await streamConnection.setRemoteDescription({
        type: 'answer',
        sdp: answer
    });
}

function connectHLS(hlsUrl) {
    console.log('📡 Connecting via HLS...');

    if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
        videoElement.src = hlsUrl;
        videoElement.play();
        loadingOverlay.style.display = 'none';
    } else {
        console.error('HLS not supported');
    }
}

function updateLiveStatus(isLive) {
    const badge = document.getElementById('live-badge');
    if (isLive) {
        badge.className = 'badge live';
        badge.innerHTML = '<div class="h-1.5 w-1.5 rounded-full bg-red-500 pulse-dot"></div>LIVE';
        chatInput.disabled = false;
        sendChatBtn.disabled = false;
    } else {
        badge.className = 'badge offline';
        badge.innerHTML = '<div class="h-1.5 w-1.5 rounded-full bg-slate-500"></div>OFFLINE';
        chatInput.disabled = true;
        sendChatBtn.disabled = true;
    }
}

// === CHAT FUNCTIONALITY ===

function addChatMessage(username, message, color = '#06b6d4') {
    const chatMessages = document.getElementById('chat-messages');
    const messageEl = document.createElement('div');
    messageEl.className = 'chat-message';
    messageEl.innerHTML = `
        <span class="username" style="color: ${color}">${username}</span>
        <span class="message">: ${message}</span>
    `;

    // Remove placeholder if exists
    const placeholder = chatMessages.querySelector('.text-center');
    if (placeholder) {
        placeholder.remove();
    }

    chatMessages.appendChild(messageEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendChatMessage() {
    const message = chatInput.value.trim();
    if (message) {
        addChatMessage('You', message);
        chatInput.value = '';
    }
}

// === INITIALIZE ===

function initializeStream() {
    console.log('🚀 Initializing live stream page...');

    // Event listeners
    playPauseBtn.addEventListener('click', togglePlayPause);
    videoElement.addEventListener('click', togglePlayPause);
    volumeBtn.addEventListener('click', toggleMute);

    // Volume slider
    const volumeSlider = document.querySelector('.volume-slider');
    volumeSlider.addEventListener('click', (e) => {
        const rect = volumeSlider.getBoundingClientRect();
        const percent = ((e.clientX - rect.left) / rect.width) * 100;
        currentVolume = Math.max(0, Math.min(100, percent));
        videoElement.volume = currentVolume / 100;
        document.querySelector('.volume-fill').style.width = currentVolume + '%';

        if (currentVolume === 0) {
            isMuted = true;
            volumeBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
        } else {
            isMuted = false;
            volumeBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
        }
    });

    // Quality selector
    qualityBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        qualityMenu.classList.toggle('show');
    });

    document.addEventListener('click', () => {
        qualityMenu.classList.remove('show');
    });

    document.querySelectorAll('.quality-option').forEach(option => {
        option.addEventListener('click', (e) => {
            const quality = e.target.dataset.quality;
            document.querySelectorAll('.quality-option').forEach(opt => opt.classList.remove('active'));
            e.target.classList.add('active');
            document.getElementById('quality-text').textContent = quality;
            console.log('Quality changed to:', quality);
        });
    });

    // Theater mode
    theaterBtn.addEventListener('click', () => {
        isTheaterMode = !isTheaterMode;
        document.body.classList.toggle('theater-mode');

        if (isTheaterMode) {
            theaterBtn.innerHTML = '<i class="fas fa-compress-wide"></i>';
        } else {
            theaterBtn.innerHTML = '<i class="fas fa-expand-wide"></i>';
        }
    });

    // Fullscreen
    fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            videoContainer.requestFullscreen().catch(err => {
                console.log('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    });

    // Fullscreen change event
    document.addEventListener('fullscreenchange', () => {
        if (document.fullscreenElement) {
            fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    });

    // Show/hide controls
    let controlsTimeout;
    videoContainer.addEventListener('mousemove', () => {
        videoContainer.classList.add('show-controls');
        clearTimeout(controlsTimeout);
        controlsTimeout = setTimeout(() => {
            if (isPlaying) {
                videoContainer.classList.remove('show-controls');
            }
        }, 3000);
    });

    videoContainer.addEventListener('mouseleave', () => {
        if (isPlaying) {
            videoContainer.classList.remove('show-controls');
        }
    });

    // Chat
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && chatInput.value.trim()) {
            sendChatMessage();
        }
    });

    sendChatBtn.addEventListener('click', sendChatMessage);

    // Auto-connect to stream
    setTimeout(() => {
        connectToStream();
    }, 1000);

    // Simulate viewer count updates
    setInterval(() => {
        const viewers = Math.floor(Math.random() * 50) + 10;
        document.getElementById('viewer-count').textContent = viewers;
    }, 5000);

    console.log('✅ Stream page ready');
}

// Start the stream
document.addEventListener('DOMContentLoaded', initializeStream);
