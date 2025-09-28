class AutomaticModeApp {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Mode toggle
        document.getElementById('modeToggle').addEventListener('change', this.handleModeToggle.bind(this));
        
        // Automatic mode functionality
        document.getElementById('showDashboardBtn').addEventListener('click', this.handleShowDashboard.bind(this));
    }

    handleModeToggle(e) {
        if (!e.target.checked) {
            // Switch to Manual mode
            window.location.href = '/';
        }
    }

    handleShowDashboard() {
        const repoUrl = document.getElementById('autoRepoUrl').value.trim();
        
        if (!repoUrl) {
            this.showDashboardMessage('Please enter a repository URL to show the dashboard.');
            return;
        }
        
        // For now, just show a message since we're not implementing functionality yet
        this.showDashboardMessage(`Dashboard loading for repository: ${repoUrl}`);
        
        // TODO: Implement actual dashboard functionality
        console.log('Show dashboard for:', repoUrl);
    }

    showDashboardMessage(message) {
        console.log('Dashboard message:', message);
        
        const dashboardContent = document.querySelector('.dashboard-content');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'dashboard-message';
        messageDiv.style.cssText = `
            background-color: #4CAF50;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
        `;
        messageDiv.textContent = message;
        
        // Remove any existing messages
        const existingMessage = dashboardContent.querySelector('.dashboard-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Add new message at the top
        dashboardContent.insertBefore(messageDiv, dashboardContent.firstChild);
        
        // Remove message after 3 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 3000);
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
}

// Initialize app when page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new AutomaticModeApp();
});