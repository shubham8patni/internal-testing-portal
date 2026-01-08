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
            let executionProgress = executions[executionId] || {};

            console.log(`[DEBUG] Looking for progress of execution: ${executionId}`);
            console.log(`[DEBUG] Available execution IDs in progress data: ${Object.keys(executions)}`);
            console.log(`[DEBUG] Initial progress data found:`, executionProgress);

            // Fallback: If no progress found for the execution ID, try to find it by combination matching
            if (!executionProgress || Object.keys(executionProgress).length === 0) {
                console.log(`[DEBUG] No progress found for ${executionId}, trying fallback matching`);

                // Extract combination from execution ID
                const execParts = executionId.split('_');
                if (execParts.length >= 3) {
                    const execCombination = execParts.slice(-3).join('_');
                    console.log(`[DEBUG] Looking for combination: ${execCombination}`);

                    // Look for any backend execution that matches this combination
                    for (const [backendId, progress] of Object.entries(executions)) {
                        const backendParts = backendId.split('_');
                        if (backendParts.length >= 3) {
                            const backendCombination = backendParts.slice(-3).join('_');
                            console.log(`[DEBUG] Checking backend combination: ${backendCombination}`);
                            if (backendCombination === execCombination) {
                                executionProgress = progress;
                                console.log(`[DEBUG] ✅ Found matching progress via fallback: ${backendId} -> ${executionId}`);
                                break;
                            }
                        }
                    }
                }
            }

            console.log(`[DEBUG] Final progress data for ${executionId}:`, executionProgress);

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

    // Map backend progress execution IDs to frontend execution IDs
    function mapExecutionIds(backendExecutions, frontendExecutionIds) {
        const progressMapping = {};
        const backendIds = Object.keys(backendExecutions);

        console.log('[ID-MAP] ========== STARTING EXECUTION ID MAPPING ==========');
        console.log('[ID-MAP] ========== STARTING EXECUTION ID MAPPING ==========');
        console.log('[ID-MAP] Backend execution IDs:', backendIds);
        console.log('[ID-MAP] Frontend execution IDs:', frontendExecutionIds);
        console.log('[ID-MAP] Backend executions count:', backendIds.length);
        console.log('[ID-MAP] Frontend executions count:', frontendExecutionIds.length);

        backendIds.forEach(backendId => {
            console.log(`[ID-MAP] Processing backend ID: ${backendId}`);
            // Backend format: sess_sess_20260107_230800_MV4_SOMPO_COMPREHENSIVE
            // Frontend format: sess_DEV_MV4_SOMPO_COMPREHENSIVE

            // Extract combination part (last 3 segments: MV4_SOMPO_COMPREHENSIVE)
            const parts = backendId.split('_');
            console.log(`[ID-MAP] Backend ID parts:`, parts);

            if (parts.length >= 3) {
                const combinationPart = parts.slice(-3).join('_');
                console.log(`[ID-MAP] Extracted combination: ${combinationPart}`);

                // Find matching frontend execution ID that ends with the same combination
                const matchingFrontendId = frontendExecutionIds.find(frontendId => {
                    const endsWith = frontendId.endsWith(combinationPart);
                    console.log(`[ID-MAP] Checking frontend ID ${frontendId}: endsWith(${combinationPart}) = ${endsWith}`);
                    return endsWith;
                });

                if (matchingFrontendId) {
                    progressMapping[matchingFrontendId] = backendExecutions[backendId];
                    console.log(`[ID-MAP] ✅ SUCCESSFUL MAPPING: ${backendId} -> ${matchingFrontendId}`);
                } else {
                    console.warn(`[ID-MAP] ⚠️  NO MATCH FOUND for backend ID: ${backendId} (combination: ${combinationPart})`);
                    console.warn(`[ID-MAP] Available frontend IDs for matching:`, frontendExecutionIds);
                }
            } else {
                console.error(`[ID-MAP] ❌ INVALID BACKEND ID FORMAT: ${backendId} (only ${parts.length} parts)`);
            }
        });

        console.log('[ID-MAP] ========== MAPPING COMPLETE ==========');
        console.log('[ID-MAP] Successfully mapped executions:', Object.keys(progressMapping).length);
        console.log('[ID-MAP] Final mapping result:', Object.keys(progressMapping));
        console.log('[ID-MAP] ======================================');

        return progressMapping;
    }

    // Load execution progress and overall status
    async function loadExecutionProgressData() {
        try {
            console.log('[DEBUG] Loading execution progress for session:', sessionId);
            console.log('[DEBUG] Current executionIds state:', executionIds);

            const data = await window.testingPortal.apiCall(`/api/execution/progress/${sessionId}`);
            console.log('[DEBUG] Raw progress response:', data);
            console.log('[DEBUG] Backend execution IDs in response:', Object.keys(data.executions || {}));

            // Apply ID mapping to bridge backend progress format with frontend execution IDs
            let mappedExecutions = {};

            if (executionIds && executionIds.length > 0) {
                console.log('[DEBUG] Using executionIds for mapping:', executionIds);
                mappedExecutions = mapExecutionIds(data.executions || {}, executionIds);
            } else {
                console.warn('[WARN] No executionIds available, attempting to infer from progress data');
                // Fallback: try to use backend data directly
                // This handles cases where sessionStorage is missing but progress API has data
                mappedExecutions = data.executions || {};

                // Try to extract frontend-style IDs from backend data
                const backendIds = Object.keys(mappedExecutions);
                if (backendIds.length > 0) {
                    // Extract combination parts and create frontend-style IDs
                    const inferredFrontendIds = backendIds.map(backendId => {
                        const parts = backendId.split('_');
                        if (parts.length >= 3) {
                            const combinationPart = parts.slice(-3).join('_');
                            return `sess_DEV_${combinationPart}`; // Assume DEV environment
                        }
                        return backendId;
                    });

                    console.log('[WARN] Inferred frontend IDs:', inferredFrontendIds);
                    mappedExecutions = mapExecutionIds(data.executions || {}, inferredFrontendIds);
                }
            }

            // Fallback: if mapping failed completely, show warning and use raw data
            if (Object.keys(mappedExecutions).length === 0 && Object.keys(data.executions || {}).length > 0) {
                console.warn('[ID-MAP] ⚠️  No successful ID mappings found! Using raw backend data as fallback.');
                console.warn('[ID-MAP] This may cause progress display issues.');
                window.executionProgressData = data;
            } else {
                // Store globally with mapped execution IDs for individual execution loading
                window.executionProgressData = {
                    ...data,
                    executions: mappedExecutions
                };
                console.log('[DEBUG] Mapped progress data available:', Object.keys(mappedExecutions));
            }

            // Update overall status
            const statusDiv = document.getElementById('overall-status');
            if (statusDiv) {
                const executions = mappedExecutions;
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
