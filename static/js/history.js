document.addEventListener('DOMContentLoaded', async () => {
    async function loadSessions() {
        try {
            const data = await window.testingPortal.apiCall('/api/session/list');
            const sessions = data.sessions;
            
            const loadingDiv = document.getElementById('loading');
            const tableContainer = document.getElementById('sessions-table-container');
            const tbody = document.getElementById('sessions-tbody');
            
            window.testingPortal.hideLoading('loading');
            tableContainer.style.display = 'block';
            
            if (sessions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px;">No sessions found</td></tr>';
                return;
            }
            
            sessions.forEach(session => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><code>${session.session_id}</code></td>
                    <td>${session.user_name}</td>
                    <td>${window.testingPortal.formatTimestamp(session.created_at)}</td>
                    <td>${window.testingPortal.createStatusBadge(session.status)}</td>
                    <td>${session.execution_count}</td>
                    <td>
                        <button onclick="navigateToExecution('${session.session_id}')" 
                                style="padding: 8px 16px; font-size: 13px;">
                            View Details
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } catch (error) {
            console.error('Error loading sessions:', error);
            window.testingPortal.hideLoading('loading');
            window.testingPortal.showError('Failed to load sessions. Please try again.');
        }
    }

    function navigateToExecution(sessionId) {
        window.testingPortal.navigateTo('/static/execution.html', { session_id: sessionId });
    }

    // Initial load
    await loadSessions();
});
