// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const POLLING_INTERVAL = 3000; // 3 seconds


// Utility Functions
function getURLParams() {
    return new URLSearchParams(window.location.search);
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function showLoading(elementId) {
    document.getElementById(elementId).style.display = 'block';
}

function hideLoading(elementId) {
    document.getElementById(elementId).style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        const p = errorDiv.querySelector('p');
        if (p) p.textContent = message;
        errorDiv.style.display = 'block';
    }
}

function createStatusBadge(status) {
    const badge = document.createElement('span');
    badge.className = 'status-badge';
    
    switch (status.toLowerCase()) {
        case 'active':
            badge.classList.add('status-active');
            badge.textContent = 'Active';
            break;
        case 'completed':
            badge.classList.add('status-completed');
            badge.textContent = 'Completed';
            break;
        case 'failed':
            badge.classList.add('status-failed');
            badge.textContent = 'Failed';
            break;
        case 'in_progress':
            badge.classList.add('status-in-progress');
            badge.textContent = 'In Progress';
            break;
        default:
            badge.textContent = status;
    }
    
    return badge;
}

// API Call Function
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Auto-refresh function for polling
function startPolling(callback, interval = POLLING_INTERVAL) {
    return setInterval(callback, interval);
}

function stopPolling(intervalId) {
    if (intervalId) {
        clearInterval(intervalId);
    }
}

// Navigation
function navigateTo(page, params = {}) {
    const url = new URL(`${window.location.origin}${page}`);
    Object.keys(params).forEach(key => {
        url.searchParams.set(key, params[key]);
    });
    window.location.href = url.toString();
}

// Export for use in other modules
window.testingPortal = {
    apiCall,
    showLoading,
    hideLoading,
    showError,
    createStatusBadge,
    formatTimestamp,
    getURLParams,
    startPolling,
    stopPolling,
    navigateTo,
    POLLING_INTERVAL,
    API_BASE_URL
};
