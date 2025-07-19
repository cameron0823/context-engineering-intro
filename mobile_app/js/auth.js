// Tree Service Estimator Pro - Authentication Module
class AuthService {
  constructor() {
    this.baseUrl = window.location.hostname === 'localhost' 
      ? 'http://localhost:8002/api' 
      : '/api';
    this.token = localStorage.getItem('auth_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    this.currentUser = null;
  }
  
  async login(username, password, remember = false) {
    try {
      const response = await fetch(`${this.baseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: username,
          password: password,
          grant_type: 'password'
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || 'Login failed'
        };
      }
      
      const data = await response.json();
      
      // Store tokens
      this.token = data.access_token;
      this.refreshToken = data.refresh_token;
      
      if (remember) {
        localStorage.setItem('auth_token', this.token);
        localStorage.setItem('refresh_token', this.refreshToken);
      } else {
        sessionStorage.setItem('auth_token', this.token);
        sessionStorage.setItem('refresh_token', this.refreshToken);
      }
      
      // Get user info
      const user = await this.getCurrentUser();
      
      // Store for offline access
      if (remember) {
        await this.storeOfflineCredentials(username, password, user);
      }
      
      return {
        success: true,
        user: user
      };
      
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }
  
  async getCurrentUser() {
    try {
      const response = await this.authenticatedFetch(`${this.baseUrl}/auth/me`);
      
      if (!response.ok) {
        throw new Error('Failed to get user info');
      }
      
      const user = await response.json();
      this.currentUser = user;
      
      // Store user info for offline access
      localStorage.setItem('current_user', JSON.stringify(user));
      
      return user;
      
    } catch (error) {
      console.error('Get user error:', error);
      
      // Try to get cached user
      const cachedUser = localStorage.getItem('current_user');
      if (cachedUser) {
        return JSON.parse(cachedUser);
      }
      
      throw error;
    }
  }
  
  async verifyToken() {
    // Check if we have a token
    const token = this.getToken();
    if (!token) {
      return null;
    }
    
    // Check if token is expired
    if (this.isTokenExpired(token)) {
      // Try to refresh
      const refreshed = await this.refreshAccessToken();
      if (!refreshed) {
        return null;
      }
    }
    
    // Get current user
    try {
      return await this.getCurrentUser();
    } catch (error) {
      console.error('Token verification failed:', error);
      return null;
    }
  }
  
  getToken() {
    return this.token || 
           localStorage.getItem('auth_token') || 
           sessionStorage.getItem('auth_token');
  }
  
  getRefreshToken() {
    return this.refreshToken || 
           localStorage.getItem('refresh_token') || 
           sessionStorage.getItem('refresh_token');
  }
  
  isTokenExpired(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      return Date.now() > exp;
    } catch (error) {
      return true;
    }
  }
  
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return false;
    }
    
    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      });
      
      if (!response.ok) {
        return false;
      }
      
      const data = await response.json();
      
      // Update tokens
      this.token = data.access_token;
      
      // Store new token
      if (localStorage.getItem('auth_token')) {
        localStorage.setItem('auth_token', this.token);
      } else {
        sessionStorage.setItem('auth_token', this.token);
      }
      
      return true;
      
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  }
  
  async authenticatedFetch(url, options = {}) {
    const token = this.getToken();
    
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };
    
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    // If 401, try to refresh token
    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        // Retry request with new token
        headers.Authorization = `Bearer ${this.getToken()}`;
        return fetch(url, {
          ...options,
          headers
        });
      }
    }
    
    return response;
  }
  
  logout() {
    // Clear tokens
    this.token = null;
    this.refreshToken = null;
    this.currentUser = null;
    
    // Clear storage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_user');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('refresh_token');
    
    // Clear offline credentials
    this.clearOfflineCredentials();
  }
  
  // Offline authentication support
  async storeOfflineCredentials(username, password, user) {
    try {
      // Hash password for offline storage
      const hashedPassword = await this.hashPassword(password);
      
      // Store in IndexedDB
      const db = await offline.openDB();
      const transaction = db.transaction(['offlineAuth'], 'readwrite');
      const store = transaction.objectStore('offlineAuth');
      
      await store.put({
        username: username,
        password: hashedPassword,
        user: user,
        timestamp: Date.now()
      });
      
    } catch (error) {
      console.error('Failed to store offline credentials:', error);
    }
  }
  
  async offlineLogin(username, password) {
    try {
      const db = await offline.openDB();
      const transaction = db.transaction(['offlineAuth'], 'readonly');
      const store = transaction.objectStore('offlineAuth');
      
      const data = await store.get(username);
      
      if (!data) {
        return {
          success: false,
          error: 'No offline credentials found'
        };
      }
      
      // Verify password
      const isValid = await this.verifyPassword(password, data.password);
      
      if (!isValid) {
        return {
          success: false,
          error: 'Invalid password'
        };
      }
      
      // Check if credentials are not too old (7 days)
      const maxAge = 7 * 24 * 60 * 60 * 1000;
      if (Date.now() - data.timestamp > maxAge) {
        return {
          success: false,
          error: 'Offline credentials expired'
        };
      }
      
      // Set user without token
      this.currentUser = data.user;
      localStorage.setItem('current_user', JSON.stringify(data.user));
      localStorage.setItem('offline_mode', 'true');
      
      return {
        success: true,
        user: data.user
      };
      
    } catch (error) {
      console.error('Offline login error:', error);
      return {
        success: false,
        error: 'Offline login failed'
      };
    }
  }
  
  async hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(hash))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }
  
  async verifyPassword(password, hash) {
    const passwordHash = await this.hashPassword(password);
    return passwordHash === hash;
  }
  
  clearOfflineCredentials() {
    offline.clearOfflineAuth();
    localStorage.removeItem('offline_mode');
  }
  
  isOfflineMode() {
    return localStorage.getItem('offline_mode') === 'true';
  }
  
  hasRole(requiredRole) {
    if (!this.currentUser) {
      return false;
    }
    
    const roleHierarchy = {
      'Admin': 4,
      'Manager': 3,
      'Estimator': 2,
      'Viewer': 1
    };
    
    const userLevel = roleHierarchy[this.currentUser.role] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;
    
    return userLevel >= requiredLevel;
  }
}

// Create global auth instance
window.auth = new AuthService();