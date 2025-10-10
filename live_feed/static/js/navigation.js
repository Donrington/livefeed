/* ============================================================================
   AJAX NAVIGATION - Prevents page reload, keeps camera connected
   ============================================================================ */

// Track current page
let currentPage = 'dashboard';

// Initialize navigation
document.addEventListener('DOMContentLoaded', () => {
    setupAjaxNavigation();
});

function setupAjaxNavigation() {
    // Get all navigation links
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent default page reload

            const url = link.getAttribute('href');
            const page = link.getAttribute('data-page');

            // Don't reload if already on this page
            if (page === currentPage) {
                console.log(`Already on ${page} page`);
                return;
            }

            // Load page content via AJAX
            loadPage(url, page, link);
        });
    });
}

async function loadPage(url, pageName, clickedLink) {
    console.log(`📄 Loading page: ${pageName}`);

    try {
        // Show loading indicator
        const mainContent = document.getElementById('main-content');
        mainContent.style.opacity = '0.5';

        // Fetch page content with AJAX header
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest' // Django can detect AJAX requests
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const html = await response.text();

        // Update content
        mainContent.innerHTML = html;
        mainContent.style.opacity = '1';

        // Update active nav link
        updateActiveNav(clickedLink);

        // Update current page
        currentPage = pageName;

        // Re-initialize page-specific JavaScript
        initializePageScripts(pageName);

        // Update URL without reload (optional - for browser history)
        window.history.pushState({ page: pageName }, '', url);

        console.log(`✅ Page loaded: ${pageName}`);

    } catch (error) {
        console.error(`❌ Error loading page: ${error}`);

        // Show error message
        document.getElementById('main-content').innerHTML = `
            <div class="col-span-12 md:col-span-9 lg:col-span-10">
                <div class="glass rounded-lg p-6">
                    <h2 class="text-xl font-bold text-red-500 mb-4">Error Loading Page</h2>
                    <p class="text-slate-400">${error.message}</p>
                    <button onclick="location.reload()" class="btn btn-primary mt-4">
                        <i class="fas fa-sync-alt mr-2"></i>
                        Reload Page
                    </button>
                </div>
            </div>
        `;
        document.getElementById('main-content').style.opacity = '1';
    }
}

function updateActiveNav(clickedLink) {
    // Remove active class from all links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('bg-slate-800/70', 'text-cyan-400', 'active');
        link.classList.add('text-slate-400');
    });

    // Add active class to clicked link
    clickedLink.classList.remove('text-slate-400');
    clickedLink.classList.add('bg-slate-800/70', 'text-cyan-400', 'active');
}

function initializePageScripts(pageName) {
    console.log(`🔄 Initializing scripts for: ${pageName}`);

    // Initialize page-specific functionality
    switch(pageName) {
        case 'dashboard':
            // Dashboard already has WebSocket connection running
            // Don't reinitialize to preserve camera connection
            console.log('Dashboard: Keeping existing connections');
            break;

        case 'settings':
            // Reinitialize settings page WebSocket
            if (typeof initSettings === 'function') {
                initSettings();
            }
            break;

        case 'analytics':
            // Initialize analytics if needed
            if (typeof initAnalytics === 'function') {
                initAnalytics();
            }
            break;

        case 'recordings':
            // Initialize recordings if needed
            if (typeof initRecordings === 'function') {
                initRecordings();
            }
            break;
    }
}

// Handle browser back/forward buttons
window.addEventListener('popstate', (event) => {
    if (event.state && event.state.page) {
        const page = event.state.page;
        const link = document.querySelector(`[data-page="${page}"]`);
        if (link) {
            const url = link.getAttribute('href');
            loadPage(url, page, link);
        }
    }
});
