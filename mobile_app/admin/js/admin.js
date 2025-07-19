// Admin Dashboard JavaScript

class AdminApp {
    constructor() {
        this.currentEstimate = null;
        this.currentUser = null;
        this.init();
    }

    async init() {
        // Check authentication
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '../index.html';
            return;
        }

        // Check if user is admin or manager
        const userRole = localStorage.getItem('userRole');
        if (!['admin', 'manager'].includes(userRole)) {
            this.showToast('Access denied. Admin or Manager role required.', 'error');
            setTimeout(() => {
                window.location.href = '../index.html';
            }, 2000);
            return;
        }

        // Display user info
        document.getElementById('username').textContent = localStorage.getItem('username') || 'Admin';
        document.getElementById('userRole').textContent = userRole.charAt(0).toUpperCase() + userRole.slice(1);

        // Setup event listeners
        this.setupEventListeners();

        // Load initial data
        await this.loadDashboard();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(link.dataset.section);
            });
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            localStorage.clear();
            window.location.href = '../index.html';
        });

        // Estimate filter
        document.getElementById('estimateFilter').addEventListener('change', () => {
            this.loadEstimates();
        });

        // Close modals on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        // Load section data
        switch(sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'estimates':
                this.loadEstimates();
                break;
            case 'pricing':
                this.loadPricing();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'reports':
                this.loadReports();
                break;
        }
    }

    async loadDashboard() {
        try {
            // Get dashboard stats
            const [estimates, users] = await Promise.all([
                api.get('/estimates/'),
                api.get('/auth/users/')
            ]);

            // Update stats
            const today = new Date().toDateString();
            const todayEstimates = estimates.filter(e => 
                new Date(e.created_at).toDateString() === today
            );
            const pendingEstimates = estimates.filter(e => e.status === 'pending');
            
            document.getElementById('todayEstimates').textContent = todayEstimates.length;
            document.getElementById('pendingApproval').textContent = pendingEstimates.length;
            
            // Calculate month revenue
            const currentMonth = new Date().getMonth();
            const monthRevenue = estimates
                .filter(e => e.status === 'approved' && new Date(e.created_at).getMonth() === currentMonth)
                .reduce((sum, e) => sum + parseFloat(e.final_total), 0);
            document.getElementById('monthRevenue').textContent = `$${monthRevenue.toFixed(2)}`;
            
            // Active users (mock data for now)
            document.getElementById('activeUsers').textContent = users.filter(u => u.is_active).length;

            // Load recent activity
            this.loadRecentActivity();
        } catch (error) {
            this.showToast('Failed to load dashboard data', 'error');
        }
    }

    async loadRecentActivity() {
        // Mock recent activity - in production, this would come from an activity log endpoint
        const activities = [
            {
                type: 'estimate',
                title: 'New estimate created',
                details: 'John Doe - $2,450.00',
                time: '5 minutes ago'
            },
            {
                type: 'user',
                title: 'User login',
                details: 'Mike Smith logged in',
                time: '15 minutes ago'
            },
            {
                type: 'system',
                title: 'Pricing updated',
                details: 'Climber rate changed to $45/hour',
                time: '1 hour ago'
            }
        ];

        const activityList = document.getElementById('activityList');
        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.type}">
                    ${activity.type === 'estimate' ? '📋' : activity.type === 'user' ? '👤' : '⚙️'}
                </div>
                <div class="activity-details">
                    <h4>${activity.title}</h4>
                    <p>${activity.details}</p>
                </div>
                <span class="activity-time">${activity.time}</span>
            </div>
        `).join('');
    }

    async loadEstimates() {
        try {
            const estimates = await api.get('/estimates/');
            const filter = document.getElementById('estimateFilter').value;
            
            let filteredEstimates = estimates;
            if (filter !== 'all') {
                filteredEstimates = estimates.filter(e => e.status === filter);
            }

            const tbody = document.getElementById('estimatesTableBody');
            tbody.innerHTML = filteredEstimates.map(estimate => `
                <tr>
                    <td>${estimate.id}</td>
                    <td>${estimate.customer_name}</td>
                    <td>$${parseFloat(estimate.final_total).toFixed(2)}</td>
                    <td><span class="status-badge ${estimate.status}">${estimate.status}</span></td>
                    <td>${new Date(estimate.created_at).toLocaleDateString()}</td>
                    <td>
                        <button class="action-btn" onclick="adminApp.viewEstimate(${estimate.id})">View</button>
                        ${estimate.status === 'pending' ? `
                            <button class="action-btn" onclick="adminApp.approveEstimate(${estimate.id})">Approve</button>
                            <button class="action-btn" onclick="adminApp.rejectEstimate(${estimate.id})">Reject</button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            this.showToast('Failed to load estimates', 'error');
        }
    }

    async viewEstimate(id) {
        try {
            const estimate = await api.get(`/estimates/${id}`);
            this.currentEstimate = estimate;

            const details = document.getElementById('estimateDetails');
            details.innerHTML = `
                <div class="estimate-details">
                    <h3>Customer Information</h3>
                    <p><strong>Name:</strong> ${estimate.customer_name}</p>
                    <p><strong>Address:</strong> ${estimate.customer_address}</p>
                    <p><strong>Phone:</strong> ${estimate.customer_phone}</p>
                    
                    <h3>Job Details</h3>
                    <p><strong>Description:</strong> ${estimate.description}</p>
                    <p><strong>Travel Distance:</strong> ${estimate.travel_miles} miles</p>
                    <p><strong>Estimated Hours:</strong> ${estimate.estimated_hours}</p>
                    <p><strong>Crew Size:</strong> ${estimate.crew_size}</p>
                    
                    <h3>Cost Breakdown</h3>
                    <p><strong>Labor Cost:</strong> $${estimate.labor_cost}</p>
                    <p><strong>Equipment Cost:</strong> $${estimate.equipment_cost}</p>
                    <p><strong>Travel Cost:</strong> $${estimate.travel_cost}</p>
                    <p><strong>Overhead:</strong> $${estimate.overhead_cost}</p>
                    <p><strong>Profit:</strong> $${estimate.profit_margin}</p>
                    <hr>
                    <p><strong>Final Total:</strong> $${estimate.final_total}</p>
                </div>
            `;

            this.openModal('estimateModal');
        } catch (error) {
            this.showToast('Failed to load estimate details', 'error');
        }
    }

    async approveEstimate(id) {
        if (!id && this.currentEstimate) {
            id = this.currentEstimate.id;
        }

        try {
            await api.post(`/estimates/${id}/approve`, {});
            this.showToast('Estimate approved successfully', 'success');
            this.closeModal('estimateModal');
            this.loadEstimates();
        } catch (error) {
            this.showToast('Failed to approve estimate', 'error');
        }
    }

    async rejectEstimate(id) {
        if (!id && this.currentEstimate) {
            id = this.currentEstimate.id;
        }

        const reason = prompt('Please provide a reason for rejection:');
        if (!reason) return;

        try {
            await api.post(`/estimates/${id}/reject`, { reason });
            this.showToast('Estimate rejected', 'info');
            this.closeModal('estimateModal');
            this.loadEstimates();
        } catch (error) {
            this.showToast('Failed to reject estimate', 'error');
        }
    }

    async loadPricing() {
        try {
            const costs = await api.get('/costs/current');
            
            // Labor rates
            document.getElementById('climberRate').value = costs.labor_rates?.climber || 45.00;
            document.getElementById('groundsmanRate').value = costs.labor_rates?.groundsman || 25.00;
            document.getElementById('driverRate').value = costs.labor_rates?.driver || 25.00;
            
            // Business rules
            document.getElementById('overheadPercent').value = costs.overhead_percent || 25.0;
            document.getElementById('profitPercent').value = costs.profit_percent || 35.0;
            document.getElementById('safetyBufferPercent').value = costs.safety_buffer_percent || 10.0;
            
            // Vehicle & Equipment
            document.getElementById('vehicleRate').value = costs.vehicle_rate_per_mile || 0.65;
            document.getElementById('chipperRate').value = costs.equipment_rates?.chipper || 75.00;
            document.getElementById('bucketTruckRate').value = costs.equipment_rates?.bucket_truck || 125.00;
        } catch (error) {
            this.showToast('Failed to load pricing configuration', 'error');
        }
    }

    async savePricing() {
        const pricingData = {
            labor_rates: {
                climber: parseFloat(document.getElementById('climberRate').value),
                groundsman: parseFloat(document.getElementById('groundsmanRate').value),
                driver: parseFloat(document.getElementById('driverRate').value)
            },
            overhead_percent: parseFloat(document.getElementById('overheadPercent').value),
            profit_percent: parseFloat(document.getElementById('profitPercent').value),
            safety_buffer_percent: parseFloat(document.getElementById('safetyBufferPercent').value),
            vehicle_rate_per_mile: parseFloat(document.getElementById('vehicleRate').value),
            equipment_rates: {
                chipper: parseFloat(document.getElementById('chipperRate').value),
                bucket_truck: parseFloat(document.getElementById('bucketTruckRate').value)
            }
        };

        try {
            await api.post('/costs/', pricingData);
            this.showToast('Pricing configuration saved successfully', 'success');
        } catch (error) {
            this.showToast('Failed to save pricing configuration', 'error');
        }
    }

    async loadUsers() {
        try {
            const users = await api.get('/auth/users/');
            
            const tbody = document.getElementById('usersTableBody');
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.email}</td>
                    <td>${user.role}</td>
                    <td><span class="status-badge ${user.is_active ? 'active' : 'inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                    <td>
                        <button class="action-btn" onclick="adminApp.editUser(${user.id})">Edit</button>
                        <button class="action-btn" onclick="adminApp.toggleUserStatus(${user.id}, ${user.is_active})">
                            ${user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            this.showToast('Failed to load users', 'error');
        }
    }

    showAddUserModal() {
        this.currentUser = null;
        document.getElementById('userModalTitle').textContent = 'Add New User';
        document.getElementById('userForm').reset();
        document.getElementById('userPassword').required = true;
        this.openModal('userModal');
    }

    async editUser(id) {
        try {
            const user = await api.get(`/auth/users/${id}`);
            this.currentUser = user;
            
            document.getElementById('userModalTitle').textContent = 'Edit User';
            document.getElementById('userUsername').value = user.username;
            document.getElementById('userEmail').value = user.email;
            document.getElementById('userRole').value = user.role;
            document.getElementById('userPassword').required = false;
            
            this.openModal('userModal');
        } catch (error) {
            this.showToast('Failed to load user details', 'error');
        }
    }

    async saveUser() {
        const formData = {
            username: document.getElementById('userUsername').value,
            email: document.getElementById('userEmail').value,
            role: document.getElementById('userRole').value,
            password: document.getElementById('userPassword').value
        };

        try {
            if (this.currentUser) {
                // Update existing user
                if (!formData.password) {
                    delete formData.password;
                }
                await api.put(`/auth/users/${this.currentUser.id}`, formData);
                this.showToast('User updated successfully', 'success');
            } else {
                // Create new user
                await api.post('/auth/register', formData);
                this.showToast('User created successfully', 'success');
            }
            
            this.closeModal('userModal');
            this.loadUsers();
        } catch (error) {
            this.showToast('Failed to save user', 'error');
        }
    }

    async toggleUserStatus(id, currentStatus) {
        try {
            await api.put(`/auth/users/${id}`, { is_active: !currentStatus });
            this.showToast(`User ${currentStatus ? 'deactivated' : 'activated'} successfully`, 'success');
            this.loadUsers();
        } catch (error) {
            this.showToast('Failed to update user status', 'error');
        }
    }

    async loadReports() {
        // Set default date range (last 30 days)
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        document.getElementById('reportStartDate').value = startDate.toISOString().split('T')[0];
        document.getElementById('reportEndDate').value = endDate.toISOString().split('T')[0];
        
        await this.generateReport();
    }

    async generateReport() {
        const startDate = document.getElementById('reportStartDate').value;
        const endDate = document.getElementById('reportEndDate').value;
        
        try {
            const estimates = await api.get('/estimates/');
            
            // Filter estimates by date range
            const filteredEstimates = estimates.filter(e => {
                const estimateDate = new Date(e.created_at).toISOString().split('T')[0];
                return estimateDate >= startDate && estimateDate <= endDate;
            });
            
            // Generate revenue data
            const revenueByDay = {};
            filteredEstimates.forEach(estimate => {
                if (estimate.status === 'approved') {
                    const day = new Date(estimate.created_at).toLocaleDateString();
                    revenueByDay[day] = (revenueByDay[day] || 0) + parseFloat(estimate.final_total);
                }
            });
            
            // Update charts (placeholder - would use Chart.js in production)
            this.showToast('Report generated successfully', 'success');
        } catch (error) {
            this.showToast('Failed to generate report', 'error');
        }
    }

    refreshDashboard() {
        this.loadDashboard();
        this.showToast('Dashboard refreshed', 'info');
    }

    openModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
            <span class="toast-message">${message}</span>
        `;
        
        document.getElementById('toastContainer').appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize admin app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminApp = new AdminApp();
});