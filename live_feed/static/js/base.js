/* ============================================================================
   BASE JAVASCRIPT - Shared across all pages
   ============================================================================ */

// Toggle mobile sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const hamburger = document.getElementById('hamburger-menu');

    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
    hamburger.classList.toggle('active');
}

// Update time display
function updateTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
        timeElement.textContent = timeStr;
    }
}

// Initialize base functionality
function initializeBase() {
    // Update time every second
    updateTime();
    setInterval(updateTime, 1000);

    console.log('✅ Base initialized');
}

// Run on page load
document.addEventListener('DOMContentLoaded', initializeBase);
