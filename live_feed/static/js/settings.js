/* ============================================================================
   SETTINGS JAVASCRIPT
   ============================================================================ */

// WebSocket connection
let ws = null;
let reconnectInterval = null;

function switchTab(tab) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Remove active from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tab + '-tab').classList.add('active');
    event.target.classList.add('active');
}

function toggleSwitch(element) {
    element.classList.toggle('active');
}

function updateValue(id, value) {
    document.getElementById(id + '-val').textContent = value;
}

// WebSocket connection setup
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/camera/`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('✅ Settings WebSocket connected');
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'camera_status') {
                // Update slider with current camera setting from Pi
                updateSliderValue('brightness', data.brightness);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('🔌 WebSocket disconnected, attempting to reconnect...');
        if (!reconnectInterval) {
            reconnectInterval = setInterval(connectWebSocket, 3000);
        }
    };
}

// Update slider and display value from WebSocket
function updateSliderValue(setting, value) {
    const slider = document.getElementById(`${setting}-slider`);
    const valueDisplay = document.getElementById(`${setting}-val`);

    if (slider && valueDisplay) {
        slider.value = value;
        valueDisplay.textContent = value;
    }
}

// Send camera setting change to backend
function updateCameraSetting(setting, value) {
    // Update display immediately
    document.getElementById(`${setting}-val`).textContent = value;

    // Send to backend via WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
        const message = {
            type: 'camera_setting',
            setting: setting,
            value: parseInt(value)
        };
        ws.send(JSON.stringify(message));
        console.log(`📤 Sent ${setting} = ${value}`);
    } else {
        console.warn('⚠️ WebSocket not connected, cannot send setting');
    }
}

// Initialize settings
function initSettings() {
    console.log('⚙️ Settings initialized');
    connectWebSocket();
}

document.addEventListener('DOMContentLoaded', initSettings);
