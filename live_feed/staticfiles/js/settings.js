/* ============================================================================
   SETTINGS JAVASCRIPT
   ============================================================================ */

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

// Initialize settings
function initSettings() {
    console.log('⚙️ Settings initialized');
}

document.addEventListener('DOMContentLoaded', initSettings);
