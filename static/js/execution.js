document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = window.testingPortal.getURLParams();
    const sessionId = urlParams.get('session_id');
    
    if (!sessionId) {
        window.testingPortal.showError('Session ID not found. Please start from landing page.');
        return;
    }

    let pollingInterval = null;
    let currentTabId = null;

    // Load tabs
    async function loadTabs() {
        try {
            const data = await window.testingPortal.apiCall(`/api/execution/tabs/${sessionId}`);
            const tabs = data.tabs;
            
            const tabsHeader = document.getElementById('tabs-header');
            tabsHeader.innerHTML = '';
            
            if (tabs.length === 0) {
                tabsHeader.innerHTML = '<p style="color: #666;">No tabs found. Start a new test execution.</p>';
                return;
            }
            
            tabs.forEach(tab => {
                const tabElement = document.createElement('div');
                tabElement.className = `tab ${currentTabId === tab.tab_id ? 'active' : ''}`;
                tabElement.textContent = `${tab.tab_id}`;
                tabElement.onclick = () => selectTab(tab.tab_id);
                tabsHeader.appendChild(tabElement);
            });
            
            // Select first tab if none selected
            if (!currentTabId && tabs.length > 0) {
                selectTab(tabs[0].tab_id);
            }
        } catch (error) {
            console.error('Error loading tabs:', error);
            window.testingPortal.showError('Failed to load tabs');
        }
    }

    // Select tab and load progress
    async function selectTab(tabId) {
        currentTabId = tabId;
        
        // Update tab styling
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        event.target.classList.add('active');
        
        // Load tab progress
        await loadTabProgress(tabId);
    }

    // Load tab progress
    async function loadTabProgress(tabId) {
        try {
            const data = await window.testingPortal.apiCall(`/api/execution/progress/${sessionId}/${tabId}`);
            const tabContent = document.getElementById('tab-content');
            const apiCalls = data.api_calls || [];
            
            let html = `
                <h3>Tab: ${tabId}</h3>
                <div class="api-list">
            `;
            
            if (apiCalls.length === 0) {
                html += '<p style="color: #666;">No API calls yet. Waiting for execution...</p>';
            } else {
                apiCalls.forEach(call => {
                    const statusClass = call.status_code === 200 ? 'completed' : 'failed';
                    html += `
                        <div class="api-item ${statusClass}">
                            <div class="api-header">
                                <span class="api-name">${call.api_step}</span>
                                <span class="status-badge ${statusClass === 'completed' ? 'status-completed' : 'status-failed'}">
                                    ${call.status_code === 200 ? '✓' : '✗'} ${call.status_code}
                                </span>
                                <span style="font-size: 12px; color: #999;">${call.execution_time_ms}ms</span>
                            </div>
                            <div>
                                <small style="color: #666;">
                                    Environment: <strong>${call.environment.toUpperCase()}</strong> | 
                                    ${call.endpoint}
                                </small>
                            </div>
                            ${call.error ? `<div style="color: #ef473a; margin-top: 5px;">Error: ${call.error}</div>` : ''}
                        </div>
                    `;
                });
            }
            
            html += '</div>';
            tabContent.innerHTML = html;
            
        } catch (error) {
            console.error('Error loading tab progress:', error);
            window.testingPortal.showError('Failed to load tab progress');
        }
    }

    // Load overall status
    async function loadOverallStatus() {
        try {
            const data = await window.testingPortal.apiCall(`/api/execution/status/${sessionId}`);
            const statusDiv = document.getElementById('overall-status');
            
            statusDiv.innerHTML = `
                <div>
                    <span>Status:</span>
                    ${window.testingPortal.createStatusBadge(data.overall_status)}
                </div>
                <div style="margin-top: 5px; font-size: 13px;">
                    <span>Total: ${data.total_executions}</span> |
                    <span>Completed: ${data.completed_executions}</span> |
                    <span>Failed: ${data.failed_executions}</span> |
                    <span>In Progress: ${data.in_progress_executions}</span>
                </div>
            `;
        } catch (error) {
            console.error('Error loading status:', error);
        }
    }

    // Initial load
    await loadTabs();
    await loadOverallStatus();
    
    // Start polling
    pollingInterval = window.testingPortal.startPolling(async () => {
        await loadTabs();
        await loadOverallStatus();
        if (currentTabId) {
            await loadTabProgress(currentTabId);
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        window.testingPortal.stopPolling(pollingInterval);
    });
});
