document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = window.testingPortal.getURLParams();
    const sessionId = urlParams.get('session_id');
    const callId = urlParams.get('call_id');
    
    if (!sessionId || !callId) {
        window.testingPortal.showError('Session ID or Call ID not found.');
        return;
    }

    // Load API call details
    async function loadAPIDetails() {
        try {
            const data = await window.testingPortal.apiCall(`/api/execution/${sessionId}/api-call/${callId}`);
            
            const apiInfoDiv = document.getElementById('api-details');
            apiInfoDiv.innerHTML = `
                <div style="background: #fafbfc; padding: 15px; border-radius: 6px;">
                    <p><strong>API Step:</strong> ${data.api_step}</p>
                    <p><strong>Environment:</strong> ${data.environment.toUpperCase()}</p>
                    <p><strong>Endpoint:</strong> ${data.endpoint}</p>
                    <p><strong>Status Code:</strong> ${data.status_code}</p>
                    <p><strong>Execution Time:</strong> ${data.execution_time_ms}ms</p>
                    ${data.error ? `<p style="color: #ef473a;"><strong>Error:</strong> ${data.error}</p>` : ''}
                </div>
            `;
        } catch (error) {
            console.error('Error loading API details:', error);
            window.testingPortal.showError('Failed to load API details');
        }
    }

    // Load comparison
    async function loadComparison() {
        try {
            const data = await window.testingPortal.apiCall(`/api/execution/${sessionId}/comparison/${callId}`);
            
            const targetResponse = document.getElementById('target-response');
            const stagingResponse = document.getElementById('staging-response');
            const differencesList = document.getElementById('differences-list');
            
            targetResponse.textContent = JSON.stringify(data.target_response, null, 2);
            stagingResponse.textContent = JSON.stringify(data.staging_response, null, 2);
            
            // Display differences
            if (data.differences && data.differences.length > 0) {
                let html = '';
                data.differences.forEach(diff => {
                    const severityClass = diff.severity;
                    html += `
                        <div class="difference ${severityClass}">
                            <p><strong>Field:</strong> ${diff.field_path}</p>
                            <p><strong>Severity:</strong> ${diff.severity.toUpperCase()}</p>
                            <p><strong>Target Value:</strong> ${JSON.stringify(diff.target_value)}</p>
                            <p><strong>Staging Value:</strong> ${JSON.stringify(diff.staging_value)}</p>
                            <p><strong>Description:</strong> ${diff.description}</p>
                        </div>
                    `;
                });
                differencesList.innerHTML = html;
                
                // Add summary
                html += `
                    <div style="background: linear-gradient(135deg, #fafbfc 0%, #f8f9fa 100%); padding: 15px; border-radius: 6px; margin-top: 15px;">
                        <h4>Summary</h4>
                        <p>Critical: ${data.summary.critical}</p>
                        <p>Warning: ${data.summary.warning}</p>
                        <p>Info: ${data.summary.info}</p>
                        <p><strong>Total Differences:</strong> ${data.summary.total}</p>
                    </div>
                `;
                differencesList.innerHTML = html;
            } else {
                differencesList.innerHTML = '<p style="color: #38ef7d; font-weight: 600;">✓ No differences found - Responses match!</p>';
            }
        } catch (error) {
            console.error('Error loading comparison:', error);
            window.testingPortal.showError('Failed to load comparison');
        }
    }

    // Initial load
    await loadAPIDetails();
    await loadComparison();
});
