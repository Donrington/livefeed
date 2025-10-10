/* ============================================================================
   AJAX NAVIGATION - Prevents page reload, keeps camera connected
   ============================================================================ */

// Track current page and loaded resources
let currentPage = 'dashboard';
let loadedCSS = {};
let loadedJS = {};

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
        // Find the grid container and sidebar
        const gridContainer = document.querySelector('.grid.grid-cols-12');
        const sidebar = document.getElementById('sidebar');

        if (!gridContainer || !sidebar) {
            throw new Error('Required DOM elements not found');
        }

        // Show loading indicator
        gridContainer.style.opacity = '0.5';

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

        // Remove all children except sidebar
        Array.from(gridContainer.children).forEach(child => {
            if (child.id !== 'sidebar') {
                child.remove();
            }
        });

        // Insert new content after sidebar
        sidebar.insertAdjacentHTML('afterend', html);

        // Load page-specific CSS and JS
        await loadPageResources();

        gridContainer.style.opacity = '1';

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
        const gridContainer = document.querySelector('.grid.grid-cols-12');
        const sidebar = document.getElementById('sidebar');

        if (gridContainer && sidebar) {
            // Remove all except sidebar
            Array.from(gridContainer.children).forEach(child => {
                if (child.id !== 'sidebar') {
                    child.remove();
                }
            });

            sidebar.insertAdjacentHTML('afterend', `
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
            `);
            gridContainer.style.opacity = '1';
        }
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

// Load page-specific CSS and JavaScript dynamically
async function loadPageResources() {
    const metadata = document.getElementById('page-metadata');
    if (!metadata) {
        console.log('No page metadata found');
        return;
    }

    const pageCss = metadata.dataset.css;
    const pageJs = metadata.dataset.js;
    const pageName = metadata.dataset.page;
    const externalJs = metadata.dataset.externalJs;

    console.log(`🎨 Loading resources for: ${pageName}`);
    console.log(`  CSS: ${pageCss}`);
    console.log(`  External JS: ${externalJs}`);
    console.log(`  JS: ${pageJs}`);

    // Load CSS
    if (pageCss && !loadedCSS[pageCss]) {
        await loadCSS(pageCss);
        loadedCSS[pageCss] = true;
    }

    // Load external JavaScript (CDN libraries) first
    if (externalJs && !loadedJS[externalJs]) {
        await loadScriptFromUrl(externalJs);
        loadedJS[externalJs] = true;
    }

    // Load page JavaScript after external dependencies
    if (pageJs && !loadedJS[pageJs]) {
        await loadScript(pageJs);
        loadedJS[pageJs] = true;
    }
}

// Dynamically load CSS file
function loadCSS(cssPath) {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (document.querySelector(`link[href*="${cssPath}"]`)) {
            console.log(`CSS already loaded: ${cssPath}`);
            resolve();
            return;
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `/static/${cssPath}`;
        link.onload = () => {
            console.log(`✅ CSS loaded: ${cssPath}`);
            resolve();
        };
        link.onerror = () => {
            console.error(`❌ Failed to load CSS: ${cssPath}`);
            reject();
        };
        document.head.appendChild(link);
    });
}

// Dynamically load JavaScript file from static folder
function loadScript(jsPath) {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (document.querySelector(`script[src*="${jsPath}"]`)) {
            console.log(`JS already loaded: ${jsPath}`);
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = `/static/${jsPath}`;
        script.onload = () => {
            console.log(`✅ JS loaded: ${jsPath}`);
            resolve();
        };
        script.onerror = () => {
            console.error(`❌ Failed to load JS: ${jsPath}`);
            reject();
        };
        document.body.appendChild(script);
    });
}

// Dynamically load JavaScript file from full URL (CDN)
function loadScriptFromUrl(url) {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (document.querySelector(`script[src="${url}"]`)) {
            console.log(`External JS already loaded: ${url}`);
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = url;
        script.onload = () => {
            console.log(`✅ External JS loaded: ${url}`);
            resolve();
        };
        script.onerror = () => {
            console.error(`❌ Failed to load external JS: ${url}`);
            reject();
        };
        document.body.appendChild(script);
    });
}
