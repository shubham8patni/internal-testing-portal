document.addEventListener('DOMContentLoaded', async () => {
    console.log('[DEBUG] ==========================================');
    console.log('[DEBUG] Execution page DOMContentLoaded fired');
    console.log('[DEBUG] ==========================================');

    const urlParams = window.testingPortal.getURLParams();
    console.log('[DEBUG] URL params object:', urlParams);
    const sessionId = urlParams.get('session_id');
    console.log('[DEBUG] Session ID extracted from URL:', sessionId);

    if (!sessionId) {
        console.error('[ERROR] Session ID not found in URL params');
        window.testingPortal.showError('Session ID not found. Please start from landing page.');
        return;
    }

    console.log('[DEBUG] Session ID validation passed, initializing...');

    let pollingInterval = null;
    let currentTabId = null;

    // Load tabs
    async function loadTabs() {
        try {
            console.log('[DEBUG] Loading tabs for session:', sessionId);
            const data = await window.testingPortal.apiCall(`/api/execution/tabs/${sessionId}`);
            console.log('[DEBUG] API response:', data);
            const tabs = data.tabs;
            console.log('[DEBUG] Tabs loaded:', tabs);
            console.log('[DEBUG] Number of tabs:', tabs ? tabs.length : 0);

            const tabsHeader = document.getElementById('tabs-header');
            console.log('[DEBUG] Tabs header element:', tabsHeader);

            if (!tabsHeader) {
                console.error('[ERROR] tabs-header element not found!');
                return;
            }

            tabsHeader.innerHTML = '';

            if (!tabs || tabs.length === 0) {
                console.warn('[WARN] No tabs found in response');
                tabsHeader.innerHTML = '<p style="color: #666;">No tabs found. Start a new test execution.</p>';
                return;
            }

            tabs.forEach((tab, index) => {
                console.log(`[DEBUG] Creating tab ${index + 1}:`, tab);
                const tabElement = document.createElement('div');
                tabElement.className = `tab ${currentTabId === tab.tab_id ? 'active' : ''}`;
                tabElement.textContent = `${tab.tab_id}`;
                tabElement.onclick = () => selectTab(tab.tab_id);
                tabsHeader.appendChild(tabElement);
                console.log(`[DEBUG] Tab ${index + 1} appended to DOM`);
            });

            console.log('[DEBUG] All tabs rendered. Total tabs in DOM:', tabsHeader.children.length);

            // Select first tab if none selected
            if (!currentTabId && tabs.length > 0) {
                console.log('[DEBUG] Auto-selecting first tab:', tabs[0].tab_id);
                selectTab(tabs[0].tab_id);
            }
        } catch (error) {
            console.error('[ERROR] Error loading tabs:', error);
            console.error('[ERROR] Error stack:', error.stack);
            window.testingPortal.showError('Failed to load tabs');
        }
    }

    // Select tab and load progress
    async function selectTab(tabId) {
        console.log('[DEBUG] selectTab called with tabId:', tabId);
        currentTabId = tabId;
        
        // Update tab styling
        const allTabs = document.querySelectorAll('.tab');
        console.log('[DEBUG] Found tabs in DOM:', allTabs.length);
        allTabs.forEach(tab => {
            tab.classList.remove('active');
        });

        // Find the clicked tab element
        const clickedTab = document.querySelector(`.tab`)?.[0];
        if (!clickedTab) {
            console.error('[ERROR] No tab elements found in DOM');
            return;
        }

        clickedTab.classList.add('active');
        console.log('[DEBUG] Tab activated:', tabId);
        
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
            console.log('[DEBUG] Loading overall status for session:', sessionId);
            const data = await window.testingPortal.apiCall(`/api/execution/status/${sessionId}`);
            console.log('[DEBUG] Overall status response:', data);
            const statusDiv = document.getElementById('overall-status');
            
            if (!statusDiv) {
                console.error('[ERROR] overall-status element not found!');
                return;
            }
            
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
            console.log('[DEBUG] Overall status rendered');
        } catch (error) {
            console.error('[ERROR] Error loading overall status:', error);
            console.error('[ERROR] Error stack:', error.stack);
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
