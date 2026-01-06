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
    let currentExecutionId = null;
    let executionIds = [];

    // Load executions from sessionStorage and create tabs
    function loadExecutions() {
        try {
            console.log('[DEBUG] Loading executions for session:', sessionId);
            const stored = sessionStorage.getItem(`${sessionId}_executions`);
            console.log('[DEBUG] Stored execution IDs:', stored);

            if (!stored) {
                console.warn('[WARN] No executions found in sessionStorage');
                const tabsHeader = document.getElementById('tabs-header');
                if (tabsHeader) {
                    tabsHeader.innerHTML = '<p style="color: #666;">No executions found. Please configure and start a test.</p>';
                }
                return;
            }

            executionIds = JSON.parse(stored);
            console.log('[DEBUG] Parsed execution IDs:', executionIds);
            console.log('[DEBUG] Number of executions:', executionIds.length);

            const tabsHeader = document.getElementById('tabs-header');
            console.log('[DEBUG] Tabs header element:', tabsHeader);

            if (!tabsHeader) {
                console.error('[ERROR] tabs-header element not found!');
                return;
            }

            tabsHeader.innerHTML = '';

            if (!executionIds || executionIds.length === 0) {
                console.warn('[WARN] No execution IDs found');
                tabsHeader.innerHTML = '<p style="color: #666;">No executions found. Start a new test execution.</p>';
                return;
            }

            executionIds.forEach((executionId, index) => {
                const tabElement = document.createElement('div');
                tabElement.className = `tab ${currentExecutionId === executionId ? 'active' : ''}`;

                // Extract display name from execution_id (category_product_plan)
                const parts = executionId.split('_');
                const displayName = parts.slice(-3).join('_'); // Last 3 parts: category_product_plan
                tabElement.textContent = displayName;
                tabElement.onclick = () => selectExecution(executionId);
                tabsHeader.appendChild(tabElement);
            });

            console.log('[DEBUG] All execution tabs rendered. Total tabs in DOM:', tabsHeader.children.length);

            // Select first execution if none selected
            if (!currentExecutionId && executionIds.length > 0) {
                console.log('[DEBUG] Auto-selecting first execution:', executionIds[0]);
                selectExecution(executionIds[0]);
            }
        } catch (error) {
            console.error('[ERROR] Error loading executions:', error);
            console.error('[ERROR] Error stack:', error.stack);
            window.testingPortal.showError('Failed to load executions');
        }
    }

    // Select execution and load progress
    function selectExecution(executionId) {
        console.log('[DEBUG] selectExecution called with executionId:', executionId);
        currentExecutionId = executionId;

        // Update tab styling
        const allTabs = document.querySelectorAll('.tab');
        console.log('[DEBUG] Found tabs in DOM:', allTabs.length);
        allTabs.forEach(tab => {
            tab.classList.remove('active');
        });

        // Find and activate the clicked tab
        allTabs.forEach((tab, index) => {
            const tabExecutionId = executionIds[index];
            if (tabExecutionId === executionId) {
                tab.classList.add('active');
                console.log('[DEBUG] Tab activated for execution:', executionId);
            }
        });

        // Load execution progress
        loadExecutionProgress(executionId);
    }

    // Load execution progress
    function loadExecutionProgress(executionId) {
        try {
            console.log('[DEBUG] Loading execution progress for:', executionId);

            // Get progress from polling data (will be updated by polling)
            const progressData = window.executionProgressData || {};
            const executions = progressData.executions || {};
            const executionProgress = executions[executionId] || {};

            const tabContent = document.getElementById('tab-content');

            // Extract display name from execution_id (category_product_plan)
            const parts = executionId.split('_');
            const displayName = parts.slice(-3).join('_');

            let html = `
                <h3>Execution: ${displayName}</h3>
                <div class="api-list">
            `;

            // Define all API steps
            const allSteps = [
                'application_submit',
                'apply_coupon',
                'payment_checkout',
                'admin_policy_list',
                'admin_policy_details',
                'customer_policy_list',
                'customer_policy_details'
            ];

            let hasAnyProgress = false;
            allSteps.forEach(step => {
                const status = executionProgress[step] || 'pending';
                hasAnyProgress = hasAnyProgress || (status !== 'pending');

                let statusClass, statusIcon, statusText;

                if (status === 'succeed') {
                    statusClass = 'completed';
                    statusIcon = '✓';
                    statusText = 'SUCCEED';
                } else if (status === 'failed') {
                    statusClass = 'failed';
                    statusIcon = '✗';
                    statusText = 'FAILED';
                } else if (status === 'can_not_proceed') {
                    statusClass = 'can_not_proceed';
                    statusIcon = '⊘';
                    statusText = 'CAN NOT PROCEED';
                } else {
                    statusClass = 'pending';
                    statusIcon = '○';
                    statusText = 'PENDING';
                }

                html += `
                    <div class="api-item ${statusClass}">
                        <div class="api-header">
                            <span class="api-name">${step.replace('_', ' ').toUpperCase()}</span>
                            <span class="status-badge ${statusClass === 'completed' ? 'status-completed' : statusClass === 'failed' ? 'status-failed' : statusClass === 'can_not_proceed' ? 'status-can-not-proceed' : 'status-pending'}">
                                ${statusIcon} ${statusText}
                            </span>
                        </div>
                    </div>
                `;
            });

            if (!hasAnyProgress) {
                html += '<p style="color: #666; margin-top: 15px;">No API calls yet. Waiting for execution...</p>';
            }

            html += '</div>';
            tabContent.innerHTML = html;

            console.log('[DEBUG] Execution progress loaded for:', executionId, executionProgress);

        } catch (error) {
            console.error('Error loading execution progress:', error);
            window.testingPortal.showError('Failed to load execution progress');
        }
    }

    // Load execution progress and overall status
    async function loadExecutionProgressData() {
        try {
            console.log('[DEBUG] Loading execution progress for session:', sessionId);
            const data = await window.testingPortal.apiCall(`/api/execution/progress/${sessionId}`);
            console.log('[DEBUG] Progress response:', data);

            // Store globally for individual execution loading
            window.executionProgressData = data;

            // Update overall status
            const statusDiv = document.getElementById('overall-status');
            if (statusDiv) {
                const executions = data.executions || {};
                const totalExecutions = Object.keys(executions).length;
                const completedExecutions = Object.values(executions).filter(exec =>
                    Object.values(exec).every(status => status === 'succeed')
                ).length;
                const failedExecutions = Object.values(executions).filter(exec =>
                    Object.values(exec).some(status => status === 'failed')
                ).length;
                const inProgressExecutions = totalExecutions - completedExecutions - failedExecutions;

                let overallStatus = 'pending';
                if (inProgressExecutions > 0) overallStatus = 'in_progress';
                else if (failedExecutions > 0) overallStatus = 'failed';
                else if (completedExecutions === totalExecutions && totalExecutions > 0) overallStatus = 'completed';

                statusDiv.innerHTML = `
                    <div>
                        <span>Status:</span>
                        ${window.testingPortal.createStatusBadge(overallStatus)}
                    </div>
                    <div style="margin-top: 5px; font-size: 13px;">
                        <span>Total: ${totalExecutions}</span> |
                        <span>Completed: ${completedExecutions}</span> |
                        <span>Failed: ${failedExecutions}</span> |
                        <span>In Progress: ${inProgressExecutions}</span>
                    </div>
                `;
                console.log('[DEBUG] Overall status updated');
            }

            // Update current execution progress if one is selected
            if (currentExecutionId) {
                loadExecutionProgress(currentExecutionId);
            }

        } catch (error) {
            console.error('[ERROR] Error loading execution progress:', error);
            console.error('[ERROR] Error stack:', error.stack);
        }
    }

    // Initial load
    loadExecutions();
    await loadExecutionProgressData();

    // Start polling
    pollingInterval = window.testingPortal.startPolling(async () => {
        await loadExecutionProgressData();
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        window.testingPortal.stopPolling(pollingInterval);
    });
});
