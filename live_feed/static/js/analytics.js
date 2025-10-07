/* ============================================================================
   ANALYTICS JAVASCRIPT
   ============================================================================ */

// Chart.js default configuration
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.1)';

// System Performance Chart
function initPerformanceChart() {
    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
    new Chart(performanceCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {
                    label: 'CPU Usage (%)',
                    data: [42, 48, 45, 51, 47, 45, 49],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Memory Usage (%)',
                    data: [58, 62, 60, 65, 63, 61, 64],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Network Usage Chart
function initNetworkChart() {
    const networkCtx = document.getElementById('networkChart').getContext('2d');
    new Chart(networkCtx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {
                    label: 'Upload (Mbps)',
                    data: [2.4, 2.8, 2.5, 3.1, 2.9, 2.7, 3.0],
                    backgroundColor: 'rgba(6, 182, 212, 0.5)',
                    borderColor: '#06b6d4',
                    borderWidth: 1
                },
                {
                    label: 'Download (Mbps)',
                    data: [1.2, 1.5, 1.3, 1.8, 1.6, 1.4, 1.7],
                    backgroundColor: 'rgba(139, 92, 246, 0.5)',
                    borderColor: '#8b5cf6',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Initialize analytics
function initAnalytics() {
    console.log('📊 Initializing Analytics...');
    initPerformanceChart();
    initNetworkChart();
    console.log('✅ Analytics Ready');
}

// Start analytics on page load
document.addEventListener('DOMContentLoaded', initAnalytics);
