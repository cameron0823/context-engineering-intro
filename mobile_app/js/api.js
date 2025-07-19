// Tree Service Estimator Pro - API Service
class APIService {
  constructor() {
    // Use the computer's IP address for API calls
    this.baseUrl = window.location.hostname === 'localhost' 
      ? 'http://localhost:8002/api' 
      : 'http://192.168.1.66:8002/api'; // Use hardwired computer's IP
    this.timeout = 30000; // 30 seconds
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Add timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    
    try {
      const response = await auth.authenticatedFetch(url, {
        ...options,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Request failed: ${response.status}`);
      }
      
      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return response;
      }
      
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      
      throw error;
    }
  }
  
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    return this.request(url, {
      method: 'GET'
    });
  }
  
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  }
  
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  }
  
  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE'
    });
  }
  
  async upload(endpoint, formData) {
    return this.request(endpoint, {
      method: 'POST',
      body: formData
    });
  }
  
  // Dashboard endpoints
  async getDashboardStats() {
    return this.get('/dashboard/stats');
  }
  
  async getRecentEstimates() {
    return this.get('/estimates/recent');
  }
  
  // Estimates endpoints
  async getEstimates(params = {}) {
    return this.get('/estimates', params);
  }
  
  async getEstimate(id) {
    return this.get(`/estimates/${id}`);
  }
  
  async createEstimate(data) {
    return this.post('/estimates', data);
  }
  
  async updateEstimate(id, data) {
    return this.put(`/estimates/${id}`, data);
  }
  
  async deleteEstimate(id) {
    return this.delete(`/estimates/${id}`);
  }
  
  async calculateEstimate(data) {
    return this.post('/estimates/calculate', data);
  }
  
  async approveEstimate(id, notes = '') {
    return this.post(`/estimates/${id}/approve`, { notes });
  }
  
  async rejectEstimate(id, reason) {
    return this.post(`/estimates/${id}/reject`, { reason });
  }
  
  async sendEstimate(id, email) {
    return this.post(`/estimates/${id}/send`, { email });
  }
  
  // Customers endpoints
  async searchCustomers(query) {
    return this.get('/customers/search', { q: query });
  }
  
  async getCustomer(id) {
    return this.get(`/customers/${id}`);
  }
  
  async createCustomer(data) {
    return this.post('/customers', data);
  }
  
  // Equipment endpoints
  async getEquipment() {
    return this.get('/equipment');
  }
  
  async getEquipmentRates() {
    return this.get('/equipment/rates');
  }
  
  // Crew endpoints
  async getCrewRates() {
    return this.get('/crew/rates');
  }
  
  // Settings endpoints
  async getSettings() {
    return this.get('/settings');
  }
  
  async updateSettings(data) {
    return this.put('/settings', data);
  }
  
  // Reports endpoints
  async getReports(type, params = {}) {
    return this.get(`/reports/${type}`, params);
  }
  
  // File upload
  async uploadPhoto(file, estimateId = null) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (estimateId) {
      formData.append('estimate_id', estimateId);
    }
    
    return this.upload('/uploads/photo', formData);
  }
  
  // Geocoding
  async reverseGeocode(lat, lng) {
    return this.get('/geocode/reverse', { lat, lng });
  }
  
  async geocodeAddress(address) {
    return this.get('/geocode/address', { address });
  }
  
  // Sync endpoints
  async syncOfflineData(data) {
    return this.post('/sync/estimates', data);
  }
  
  async getLastSync() {
    return this.get('/sync/status');
  }
  
  // Health check
  async checkHealth() {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-cache'
      });
      
      return response.ok;
    } catch (error) {
      return false;
    }
  }
  
  // Error handling wrapper
  async safeRequest(requestFunc, fallbackFunc = null) {
    try {
      return await requestFunc();
    } catch (error) {
      console.error('API request failed:', error);
      
      // If offline, try fallback
      if (!navigator.onLine && fallbackFunc) {
        return await fallbackFunc();
      }
      
      throw error;
    }
  }
}

// Create global API instance
window.api = new APIService();