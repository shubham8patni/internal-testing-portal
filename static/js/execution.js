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

                // Only make status badges clickable for succeed/failed/can_not_proceed statuses
                const isClickable = ['succeed', 'failed', 'can_not_proceed'].includes(status);
                const clickHandler = isClickable ? `onclick="openApiComparison('${executionId}', '${step}')"` : '';
                const cursorStyle = isClickable ? 'cursor: pointer;' : '';

                html += `
                    <div class="api-item ${statusClass}">
                        <div class="api-header">
                            <span class="api-name">${step.replace('_', ' ').toUpperCase()}</span>
                            <span class="status-badge api-status-badge ${statusClass === 'completed' ? 'status-completed' : statusClass === 'failed' ? 'status-failed' : statusClass === 'can_not_proceed' ? 'status-can-not-proceed' : 'status-pending'}"
                                  ${clickHandler}
                                  style="${cursorStyle}"
                                  title="${isClickable ? 'Click to compare API responses' : ''}">
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

    // ========================================
    // API COMPARISON MODAL FUNCTIONALITY
    // ========================================

    // Global modal state
    let apiComparisonModal = null;
    let targetJsonEditor = null;
    let stagingJsonEditor = null;

    // Initialize modal when page loads
    apiComparisonModal = document.getElementById('api-comparison-modal');

    // Open API comparison modal
    async function openApiComparison(executionId, apiStep) {
        console.log(`[MODAL] Opening API comparison modal for ${executionId} - ${apiStep}`);

        if (!apiComparisonModal) {
            console.error('[MODAL] Modal element not found');
            showError('Modal component not found. Please refresh the page.');
            return;
        }

        // Show modal and loading state
        apiComparisonModal.classList.remove('hidden');
        showModalLoading();

        // Update modal header
        updateModalHeader(apiStep, executionId);

        try {
            // Fetch comparison data from backend API
            const response = await window.testingPortal.apiCall(
                `/api/execution/${executionId}/compare/${apiStep}`
            );

            console.log('[MODAL] Comparison data received:', response);

            // Display comparison data
            displayApiComparison(response);

        } catch (error) {
            console.error('[MODAL] Failed to load comparison data:', error);
            showModalError('Failed to load API comparison data. Please try again.');
        }
    }

    // Close API comparison modal
    function closeApiComparisonModal() {
        console.log('[MODAL] Closing API comparison modal');

        if (apiComparisonModal) {
            apiComparisonModal.classList.add('hidden');

            // Clean up JSON editors
            cleanupJsonEditors();
        }
    }

    // Update modal header with API and execution info
    function updateModalHeader(apiStep, executionId) {
        const apiStepBadge = document.getElementById('modal-api-step');
        const executionContext = document.getElementById('modal-execution-context');

        if (apiStepBadge) {
            apiStepBadge.textContent = apiStep.replace('_', ' ').toUpperCase();
        }

        if (executionContext && executionId) {
            // Parse execution ID to show readable context
            const parts = executionId.split('_');
            if (parts.length >= 5) {
                const category = parts[2];
                const product = parts[3];
                const plan = parts[4];
                executionContext.textContent = `${category} → ${product} → ${plan}`;
            } else {
                executionContext.textContent = executionId;
            }
        }
    }

    // Display API comparison data
    function displayApiComparison(data) {
        console.log('[MODAL] Displaying API comparison data');

        // Update environment labels
        const targetEnvSpan = document.getElementById('target-env');
        if (targetEnvSpan) {
            targetEnvSpan.textContent = data.target_environment || 'DEV';
        }

        // Display target response
        displayApiResponse('target-json-container', data.target_response, 'target');

        // Display staging response
        displayApiResponse('staging-json-container', data.staging_response, 'staging');

        // Hide loading state
        hideModalLoading();
    }

    // Display individual API response
    function displayApiResponse(containerId, responseData, environment) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`[MODAL] Container ${containerId} not found`);
            return;
        }

        // Update status indicator
        updateStatusIndicator(environment, responseData);

        // Clear previous content
        container.innerHTML = '';

        try {
            // Determine what data to display
            let jsonData = null;
            let displayMode = 'view';

            if (responseData.success === false && responseData.error) {
                // Failed API call - show full error object
                jsonData = responseData.error;
                console.log(`[MODAL] Displaying error data for ${environment}:`, jsonData);
            } else if (responseData.success === true && responseData.data) {
                // Successful API call - show response data
                jsonData = responseData.data;
                console.log(`[MODAL] Displaying success data for ${environment}:`, jsonData);
            } else {
                // No data available
                jsonData = { message: 'No response data available' };
                console.log(`[MODAL] No data available for ${environment}`);
            }

            // Initialize JSONEditor
            const options = {
                mode: 'view',
                modes: ['view', 'form', 'code', 'tree'],
                onError: (error) => {
                    console.error(`[JSON-EDITOR] Error in ${environment} editor:`, error);
                }
            };

            const editor = new JSONEditor(container, options);

            // Set JSON data
            editor.set(jsonData || {});

            // Store editor reference for cleanup and copy functionality
            if (environment === 'target') {
                targetJsonEditor = editor;
            } else if (environment === 'staging') {
                stagingJsonEditor = editor;
            }

            console.log(`[MODAL] JSON editor initialized for ${environment}`);

        } catch (error) {
            console.error(`[MODAL] Failed to initialize JSON editor for ${environment}:`, error);
            container.innerHTML = `
                <div class="json-error">
                    <p>❌ Failed to display JSON data</p>
                    <pre>${JSON.stringify(responseData, null, 2)}</pre>
                </div>
            `;
        }
    }

    // Update status indicator for environment
    function updateStatusIndicator(environment, responseData) {
        const statusIndicator = document.getElementById(`${environment}-status-indicator`);

        if (statusIndicator) {
            const statusCode = responseData.status_code;
            const success = responseData.success;

            let statusText = 'UNKNOWN';
            let statusIcon = '❓';
            let statusClass = 'pending';

            if (success === true) {
                statusText = 'SUCCESS';
                statusIcon = '✅';
                statusClass = 'success';
            } else if (success === false) {
                statusText = 'FAILED';
                statusIcon = '❌';
                statusClass = 'failed';
            } else {
                statusText = 'NO DATA';
                statusIcon = '⚠️';
                statusClass = 'pending';
            }

            const codeText = statusCode ? ` (${statusCode})` : '';
            statusIndicator.textContent = `${statusIcon} ${statusText}${codeText}`;
            statusIndicator.setAttribute('data-status', statusClass);
        }
    }

    // Copy API response to clipboard
    function copyApiResponse(environment) {
        console.log(`[MODAL] Copying ${environment} response to clipboard`);

        let editor = null;
        if (environment === 'target') {
            editor = targetJsonEditor;
        } else if (environment === 'staging') {
            editor = stagingJsonEditor;
        }

        if (editor) {
            try {
                const jsonData = editor.get();
                const jsonString = JSON.stringify(jsonData, null, 2);

                navigator.clipboard.writeText(jsonString).then(() => {
                    showCopyFeedback(environment);
                }).catch(err => {
                    console.error('[MODAL] Failed to copy to clipboard:', err);
                    // Fallback: try older clipboard API
                    const textArea = document.createElement('textarea');
                    textArea.value = jsonString;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    showCopyFeedback(environment);
                });
            } catch (error) {
                console.error('[MODAL] Failed to get JSON data:', error);
            }
        } else {
            console.warn(`[MODAL] No JSON editor found for ${environment}`);
        }
    }

    // Show copy feedback
    function showCopyFeedback(environment) {
        const btnSelector = environment === 'target'
            ? '.copy-btn:first-child'
            : '.copy-btn:nth-child(2)';

        const btn = document.querySelector(btnSelector);
        if (btn) {
            const originalText = btn.textContent;
            btn.textContent = '✅ Copied!';
            btn.style.background = '#28a745';
            btn.style.color = 'white';
            btn.style.borderColor = '#28a745';

            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
                btn.style.color = '';
                btn.style.borderColor = '';
            }, 2000);
        }
    }

    // Show modal loading state
    function showModalLoading() {
        const containers = ['target-json-container', 'staging-json-container'];
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="json-loading">
                        <div class="spinner"></div>
                        <p>Loading API response...</p>
                    </div>
                `;
            }
        });
    }

    // Hide modal loading state
    function hideModalLoading() {
        // Loading is hidden when displayApiComparison() completes
    }

    // Show modal error state
    function showModalError(message) {
        const containers = ['target-json-container', 'staging-json-container'];
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="json-error">
                        <p>❌ ${message}</p>
                    </div>
                `;
            }
        });
    }

    // Clean up JSON editors
    function cleanupJsonEditors() {
        if (targetJsonEditor) {
            try {
                targetJsonEditor.destroy();
            } catch (e) {
                console.warn('[MODAL] Error cleaning up target editor:', e);
            }
            targetJsonEditor = null;
        }

        if (stagingJsonEditor) {
            try {
                stagingJsonEditor.destroy();
            } catch (e) {
                console.warn('[MODAL] Error cleaning up staging editor:', e);
            }
            stagingJsonEditor = null;
        }
    }

    // Keyboard navigation
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && apiComparisonModal && !apiComparisonModal.classList.contains('hidden')) {
            closeApiComparisonModal();
        }
    });

    // Make functions globally available
    window.openApiComparison = openApiComparison;
    window.closeApiComparisonModal = closeApiComparisonModal;
    window.copyApiResponse = copyApiResponse;
});
