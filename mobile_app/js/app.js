// Tree Service Estimator Pro - Main App
class TreeServiceApp {
  constructor() {
    this.currentUser = null;
    this.currentPage = 'dashboard';
    this.currentStep = 1;
    this.estimateData = {};
    this.photos = [];
    this.isOnline = navigator.onLine;
    
    this.init();
  }
  
  init() {
    // Check authentication
    this.checkAuth();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Initialize offline functionality
    this.initOfflineSupport();
    
    // Setup navigation
    this.setupNavigation();
    
    // Check for PWA install prompt
    this.checkInstallPrompt();
    
    // Initialize GPS
    this.initializeGPS();
  }
  
  setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => this.handleLogin(e));
    }
    
    // Menu toggle
    document.getElementById('menu-toggle')?.addEventListener('click', () => {
      document.getElementById('nav-drawer').classList.toggle('open');
    });
    
    // Close drawer on outside click
    document.addEventListener('click', (e) => {
      const drawer = document.getElementById('nav-drawer');
      const menuToggle = document.getElementById('menu-toggle');
      if (drawer?.classList.contains('open') && 
          !drawer.contains(e.target) && 
          !menuToggle.contains(e.target)) {
        drawer.classList.remove('open');
      }
    });
    
    // Logout
    document.getElementById('logout-btn')?.addEventListener('click', () => {
      this.logout();
    });
    
    // Crew size buttons
    document.querySelectorAll('.crew-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this.selectCrewSize(e));
    });
    
    // Equipment checkboxes
    document.querySelectorAll('input[name="equipment"]').forEach(checkbox => {
      checkbox.addEventListener('change', () => this.updateEquipmentSelection());
    });
    
    // Filter chips
    document.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', (e) => this.filterEstimates(e));
    });
    
    // Search
    document.getElementById('estimate-search')?.addEventListener('input', (e) => {
      this.searchEstimates(e.target.value);
    });
    
    // Network status
    window.addEventListener('online', () => this.handleOnlineStatus(true));
    window.addEventListener('offline', () => this.handleOnlineStatus(false));
  }
  
  setupNavigation() {
    // Navigation links
    document.querySelectorAll('.nav-link[data-page], .nav-item[data-page]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.dataset.page;
        if (page) {
          this.navigateTo(page);
        }
      });
    });
    
    // Handle back button
    window.addEventListener('popstate', (e) => {
      if (e.state && e.state.page) {
        this.showPage(e.state.page);
      }
    });
  }
  
  async checkAuth() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      this.showLoginScreen();
      return;
    }
    
    try {
      const user = await auth.verifyToken();
      if (user) {
        this.currentUser = user;
        this.showMainApp();
        this.loadDashboard();
      } else {
        this.showLoginScreen();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      this.showLoginScreen();
    }
  }
  
  showLoginScreen() {
    document.getElementById('login-screen').classList.add('active');
    document.getElementById('main-app').style.display = 'none';
  }
  
  showMainApp() {
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('main-app').style.display = 'block';
    
    // Update user info
    document.getElementById('user-name').textContent = this.currentUser.name;
    document.getElementById('user-role').textContent = this.currentUser.role;
    
    // Show/hide role-specific features
    if (this.currentUser.role === 'Admin' || this.currentUser.role === 'Manager') {
      document.querySelectorAll('.manager-only').forEach(el => el.style.display = 'block');
    }
    if (this.currentUser.role === 'Admin') {
      document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'block');
    }
  }
  
  async handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const remember = document.getElementById('remember-me').checked;
    
    // Show loading
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline-block';
    submitBtn.disabled = true;
    
    try {
      const result = await auth.login(username, password, remember);
      if (result.success) {
        this.currentUser = result.user;
        this.showMainApp();
        this.loadDashboard();
      } else {
        this.showError('Invalid username or password');
      }
    } catch (error) {
      if (this.isOnline) {
        this.showError('Login failed. Please try again.');
      } else {
        // Try offline login
        const offlineResult = await auth.offlineLogin(username, password);
        if (offlineResult.success) {
          this.currentUser = offlineResult.user;
          this.showMainApp();
          this.loadDashboard();
          utils.showToast('Logged in offline', 'warning');
        } else {
          this.showError('Cannot login offline without previous online login');
        }
      }
    } finally {
      btnText.style.display = 'inline-block';
      btnLoading.style.display = 'none';
      submitBtn.disabled = false;
    }
  }
  
  showError(message) {
    const errorEl = document.getElementById('login-error');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.style.display = 'block';
      setTimeout(() => {
        errorEl.style.display = 'none';
      }, 5000);
    }
  }
  
  logout() {
    auth.logout();
    this.currentUser = null;
    this.showLoginScreen();
    this.navigateTo('dashboard'); // Reset navigation
  }
  
  navigateTo(page) {
    // Close drawer
    document.getElementById('nav-drawer').classList.remove('open');
    
    // Update active states
    document.querySelectorAll('.nav-link, .nav-item').forEach(link => {
      if (link.dataset.page === page) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
    
    // Show page
    this.showPage(page);
    
    // Update browser history
    history.pushState({ page }, '', `#${page}`);
  }
  
  showPage(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => {
      p.style.display = 'none';
      p.classList.remove('active');
    });
    
    // Show selected page
    const pageEl = document.getElementById(`${page}-page`);
    if (pageEl) {
      pageEl.style.display = 'block';
      pageEl.classList.add('active');
    }
    
    // Update header title
    const titles = {
      'dashboard': 'Dashboard',
      'new-estimate': 'New Estimate',
      'estimates': 'My Estimates',
      'approvals': 'Approvals',
      'settings': 'Settings',
      'profile': 'Profile'
    };
    
    document.getElementById('page-title').textContent = titles[page] || 'Tree Service Pro';
    this.currentPage = page;
    
    // Load page-specific content
    switch (page) {
      case 'dashboard':
        this.loadDashboard();
        break;
      case 'estimates':
        this.loadEstimates();
        break;
      case 'new-estimate':
        this.resetEstimateWizard();
        break;
    }
  }
  
  async loadDashboard() {
    try {
      const stats = await api.getDashboardStats();
      
      // Update stats
      document.getElementById('estimates-today').textContent = stats.estimatesToday || '0';
      document.getElementById('total-value').textContent = utils.formatCurrency(stats.totalValue || 0);
      
      // Load recent estimates
      const recentEstimates = await api.getRecentEstimates();
      this.displayRecentEstimates(recentEstimates);
      
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      if (!this.isOnline) {
        // Load from offline storage
        const offlineData = await offline.getDashboardData();
        if (offlineData) {
          document.getElementById('estimates-today').textContent = offlineData.estimatesToday || '0';
          document.getElementById('total-value').textContent = utils.formatCurrency(offlineData.totalValue || 0);
          this.displayRecentEstimates(offlineData.recentEstimates || []);
        }
      }
    }
  }
  
  displayRecentEstimates(estimates) {
    const container = document.getElementById('recent-estimates-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (estimates.length === 0) {
      container.innerHTML = '<p class="text-center">No recent estimates</p>';
      return;
    }
    
    estimates.forEach(estimate => {
      const card = this.createEstimateCard(estimate);
      container.appendChild(card);
    });
  }
  
  createEstimateCard(estimate) {
    const card = document.createElement('div');
    card.className = 'estimate-card';
    card.onclick = () => this.viewEstimate(estimate.id);
    
    const statusClass = `status-${estimate.status.toLowerCase()}`;
    
    card.innerHTML = `
      <div class="estimate-header">
        <span class="estimate-number">#${estimate.estimate_number}</span>
        <span class="estimate-status ${statusClass}">${estimate.status}</span>
      </div>
      <h4 class="estimate-customer">${estimate.customer_name}</h4>
      <p class="estimate-details">
        <i class="fas fa-map-marker-alt"></i> ${estimate.service_address}
      </p>
      <p class="estimate-details">
        <i class="fas fa-calendar"></i> ${utils.formatDate(estimate.created_at)}
      </p>
      <div class="estimate-amount">${utils.formatCurrency(estimate.total_amount)}</div>
    `;
    
    return card;
  }
  
  // Estimate Wizard Methods
  resetEstimateWizard() {
    this.currentStep = 1;
    this.estimateData = {};
    this.photos = [];
    
    // Reset form
    document.getElementById('estimate-form').reset();
    
    // Reset crew size
    document.querySelectorAll('.crew-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    document.querySelector('.crew-btn[data-crew="3"]').classList.add('active');
    document.getElementById('crew-size').value = '3';
    
    // Show first step
    this.showStep(1);
    
    // Clear photos
    document.getElementById('photo-preview').innerHTML = '';
    
    // Hide calculation result
    document.getElementById('calculation-result').style.display = 'none';
  }
  
  showStep(step) {
    // Update progress bar
    document.querySelectorAll('.progress-step').forEach((el, index) => {
      if (index + 1 < step) {
        el.classList.add('completed');
        el.classList.remove('active');
      } else if (index + 1 === step) {
        el.classList.add('active');
        el.classList.remove('completed');
      } else {
        el.classList.remove('active', 'completed');
      }
    });
    
    // Show/hide steps
    document.querySelectorAll('.wizard-step').forEach(el => {
      el.style.display = el.dataset.step == step ? 'block' : 'none';
    });
    
    // Update navigation buttons
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    prevBtn.style.display = step === 1 ? 'none' : 'block';
    nextBtn.innerHTML = step === 4 ? 'Finish <i class="fas fa-check"></i>' : 'Next <i class="fas fa-arrow-right"></i>';
    
    this.currentStep = step;
    
    // Update summary on step 4
    if (step === 4) {
      this.updateSummary();
    }
  }
  
  nextStep() {
    if (!this.validateStep(this.currentStep)) {
      return;
    }
    
    this.saveStepData(this.currentStep);
    
    if (this.currentStep < 4) {
      this.showStep(this.currentStep + 1);
    }
  }
  
  previousStep() {
    if (this.currentStep > 1) {
      this.showStep(this.currentStep - 1);
    }
  }
  
  validateStep(step) {
    switch (step) {
      case 1:
        const customerName = document.getElementById('customer-name').value.trim();
        const customerPhone = document.getElementById('customer-phone').value.trim();
        const serviceAddress = document.getElementById('service-address').value.trim();
        
        if (!customerName || !customerPhone || !serviceAddress) {
          utils.showToast('Please fill in all required fields', 'error');
          return false;
        }
        
        if (!utils.validatePhone(customerPhone)) {
          utils.showToast('Please enter a valid phone number', 'error');
          return false;
        }
        break;
        
      case 2:
        const jobType = document.getElementById('job-type').value;
        const jobDescription = document.getElementById('job-description').value.trim();
        
        if (!jobType || !jobDescription) {
          utils.showToast('Please select job type and provide description', 'error');
          return false;
        }
        break;
        
      case 3:
        const workHours = document.getElementById('work-hours').value;
        
        if (!workHours || workHours < 0.5) {
          utils.showToast('Please enter valid work hours', 'error');
          return false;
        }
        break;
    }
    
    return true;
  }
  
  saveStepData(step) {
    switch (step) {
      case 1:
        this.estimateData.customer_name = document.getElementById('customer-name').value;
        this.estimateData.customer_phone = document.getElementById('customer-phone').value;
        this.estimateData.customer_email = document.getElementById('customer-email').value;
        this.estimateData.service_address = document.getElementById('service-address').value;
        break;
        
      case 2:
        this.estimateData.job_type = document.getElementById('job-type').value;
        this.estimateData.job_description = document.getElementById('job-description').value;
        this.estimateData.photos = this.photos;
        break;
        
      case 3:
        this.estimateData.work_hours = parseFloat(document.getElementById('work-hours').value);
        this.estimateData.crew_size = parseInt(document.getElementById('crew-size').value);
        this.estimateData.equipment = Array.from(document.querySelectorAll('input[name="equipment"]:checked'))
          .map(cb => cb.value);
        this.estimateData.emergency_service = document.getElementById('emergency-job').checked;
        break;
    }
  }
  
  selectCrewSize(e) {
    const btn = e.currentTarget;
    const size = btn.dataset.crew;
    
    // Update active state
    document.querySelectorAll('.crew-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    // Update hidden input
    document.getElementById('crew-size').value = size === '5+' ? '5' : size;
  }
  
  updateEquipmentSelection() {
    // Could add logic here to calculate equipment costs dynamically
  }
  
  updateSummary() {
    document.getElementById('summary-customer').textContent = this.estimateData.customer_name || '';
    document.getElementById('summary-address').textContent = this.estimateData.service_address || '';
    document.getElementById('summary-job-type').textContent = 
      document.querySelector(`#job-type option[value="${this.estimateData.job_type}"]`)?.textContent || '';
    document.getElementById('summary-description').textContent = this.estimateData.job_description || '';
    document.getElementById('summary-hours').textContent = `${this.estimateData.work_hours || 0} hours`;
    document.getElementById('summary-crew').textContent = `${this.estimateData.crew_size || 0} crew members`;
    
    const equipment = this.estimateData.equipment || [];
    const equipmentText = equipment.length > 0 ? equipment.join(', ') : 'None';
    document.getElementById('summary-equipment').textContent = equipmentText;
  }
  
  async calculateEstimate() {
    utils.showLoading();
    
    try {
      const calculation = await estimates.calculateEstimate(this.estimateData);
      
      // Display results
      document.getElementById('total-amount').textContent = utils.formatCurrency(calculation.total_amount);
      document.getElementById('labor-cost').textContent = utils.formatCurrency(calculation.labor_cost);
      document.getElementById('equipment-cost').textContent = utils.formatCurrency(calculation.equipment_cost);
      document.getElementById('travel-cost').textContent = utils.formatCurrency(calculation.travel_cost);
      
      document.getElementById('calculation-result').style.display = 'block';
      
      // Store calculation
      this.estimateData.calculation = calculation;
      
    } catch (error) {
      console.error('Calculation failed:', error);
      utils.showToast('Failed to calculate estimate', 'error');
    } finally {
      utils.hideLoading();
    }
  }
  
  async saveEstimate() {
    utils.showLoading();
    
    try {
      const result = await estimates.saveEstimate(this.estimateData);
      
      if (result.success) {
        utils.showToast('Estimate saved successfully', 'success');
        
        // Navigate to estimates list
        this.navigateTo('estimates');
        
        // Reset wizard
        this.resetEstimateWizard();
      } else {
        utils.showToast('Failed to save estimate', 'error');
      }
    } catch (error) {
      console.error('Save failed:', error);
      
      if (!this.isOnline) {
        // Save offline
        const offlineResult = await estimates.saveOfflineEstimate(this.estimateData);
        if (offlineResult.success) {
          utils.showToast('Estimate saved offline. Will sync when online.', 'warning');
          this.navigateTo('estimates');
          this.resetEstimateWizard();
        } else {
          utils.showToast('Failed to save estimate offline', 'error');
        }
      } else {
        utils.showToast('Failed to save estimate', 'error');
      }
    } finally {
      utils.hideLoading();
    }
  }
  
  async shareEstimate() {
    if (navigator.share) {
      try {
        const text = `Estimate for ${this.estimateData.customer_name}\n` +
                    `Total: ${utils.formatCurrency(this.estimateData.calculation.total_amount)}\n` +
                    `Job: ${this.estimateData.job_description}`;
        
        await navigator.share({
          title: 'Tree Service Estimate',
          text: text,
          url: window.location.href
        });
      } catch (error) {
        console.log('Share cancelled or failed:', error);
      }
    } else {
      utils.showToast('Sharing not supported on this device', 'warning');
    }
  }
  
  async useCurrentLocation() {
    if (!navigator.geolocation) {
      utils.showToast('Location services not available', 'error');
      return;
    }
    
    utils.showLoading();
    
    try {
      const position = await this.getCurrentPosition();
      const address = await this.reverseGeocode(position.coords.latitude, position.coords.longitude);
      
      document.getElementById('service-address').value = address;
      
      // Store coordinates
      this.estimateData.latitude = position.coords.latitude;
      this.estimateData.longitude = position.coords.longitude;
      
    } catch (error) {
      console.error('Location error:', error);
      utils.showToast('Failed to get current location', 'error');
    } finally {
      utils.hideLoading();
    }
  }
  
  getCurrentPosition() {
    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      });
    });
  }
  
  async reverseGeocode(latitude, longitude) {
    // This would normally call a geocoding API
    // For now, return a formatted string
    return `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
  }
  
  async loadEstimates() {
    utils.showLoading();
    
    try {
      const estimates = await api.getEstimates();
      this.displayEstimates(estimates);
    } catch (error) {
      console.error('Failed to load estimates:', error);
      
      if (!this.isOnline) {
        // Load offline estimates
        const offlineEstimates = await offline.getEstimates();
        this.displayEstimates(offlineEstimates);
      }
    } finally {
      utils.hideLoading();
    }
  }
  
  displayEstimates(estimates) {
    const container = document.getElementById('estimates-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (estimates.length === 0) {
      container.innerHTML = '<p class="text-center">No estimates found</p>';
      return;
    }
    
    estimates.forEach(estimate => {
      const card = this.createEstimateCard(estimate);
      container.appendChild(card);
    });
  }
  
  filterEstimates(e) {
    const chip = e.currentTarget;
    const filter = chip.dataset.filter;
    
    // Update active state
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    
    // Apply filter
    // This would filter the displayed estimates
    console.log('Filter by:', filter);
  }
  
  searchEstimates(query) {
    // Search implementation
    console.log('Search for:', query);
  }
  
  viewEstimate(id) {
    // Navigate to estimate details
    console.log('View estimate:', id);
  }
  
  handleOnlineStatus(isOnline) {
    this.isOnline = isOnline;
    
    const indicator = document.getElementById('offline-indicator');
    if (indicator) {
      indicator.style.display = isOnline ? 'none' : 'block';
    }
    
    if (isOnline) {
      utils.showToast('Back online', 'success');
      // Trigger sync
      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        navigator.serviceWorker.ready.then(registration => {
          registration.sync.register('sync-estimates');
        });
      }
    } else {
      utils.showToast('Working offline', 'warning');
    }
  }
  
  initOfflineSupport() {
    // Initialize offline storage
    offline.init();
    
    // Check initial online status
    this.handleOnlineStatus(navigator.onLine);
  }
  
  checkInstallPrompt() {
    let deferredPrompt;
    
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      
      // Show install button
      this.showInstallPrompt(deferredPrompt);
    });
  }
  
  showInstallPrompt(deferredPrompt) {
    // Create install prompt UI
    const prompt = document.createElement('div');
    prompt.className = 'install-prompt';
    prompt.innerHTML = `
      <h3>Install Tree Service Pro</h3>
      <p>Install our app for offline access and better performance</p>
      <div class="install-buttons">
        <button class="btn btn-primary" id="install-btn">Install</button>
        <button class="btn btn-secondary" id="dismiss-btn">Not Now</button>
      </div>
    `;
    
    document.body.appendChild(prompt);
    
    // Show with animation
    setTimeout(() => prompt.classList.add('show'), 100);
    
    // Handle install
    document.getElementById('install-btn').addEventListener('click', async () => {
      prompt.classList.remove('show');
      deferredPrompt.prompt();
      
      const { outcome } = await deferredPrompt.userChoice;
      console.log('Install prompt outcome:', outcome);
      
      setTimeout(() => prompt.remove(), 300);
    });
    
    // Handle dismiss
    document.getElementById('dismiss-btn').addEventListener('click', () => {
      prompt.classList.remove('show');
      setTimeout(() => prompt.remove(), 300);
    });
  }
  
  initializeGPS() {
    if ('geolocation' in navigator) {
      // Request permission early
      navigator.permissions.query({ name: 'geolocation' }).then(result => {
        console.log('Geolocation permission:', result.state);
      });
    }
  }
  
  // Photo handling methods (delegated to camera.js)
  capturePhoto() {
    camera.capturePhoto();
  }
  
  selectPhoto() {
    camera.selectPhoto();
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new TreeServiceApp();
});