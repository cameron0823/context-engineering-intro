// Tree Service Estimator Pro - Utilities Module
class Utils {
  constructor() {
    this.toastQueue = [];
    this.isShowingToast = false;
  }
  
  // Format currency
  formatCurrency(amount) {
    if (typeof amount !== 'number' || isNaN(amount)) {
      amount = 0;
    }
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }
  
  // Format date
  formatDate(dateString, includeTime = false) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    
    const options = {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    };
    
    if (includeTime) {
      options.hour = 'numeric';
      options.minute = '2-digit';
      options.hour12 = true;
    }
    
    return new Intl.DateTimeFormat('en-US', options).format(date);
  }
  
  // Format relative time
  formatRelativeTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
      return 'just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 604800) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else {
      return this.formatDate(dateString);
    }
  }
  
  // Validate phone number
  validatePhone(phone) {
    // Remove all non-digits
    const cleaned = phone.replace(/\D/g, '');
    
    // Check if it's a valid US phone number (10 digits)
    return cleaned.length === 10 || (cleaned.length === 11 && cleaned[0] === '1');
  }
  
  // Format phone number
  formatPhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned[0] === '1') {
      return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
    }
    
    return phone;
  }
  
  // Validate email
  validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }
  
  // Debounce function
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  // Throttle function
  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
  
  // Show toast notification
  showToast(message, type = 'info', duration = 3000) {
    // Add to queue
    this.toastQueue.push({ message, type, duration });
    
    // Process queue
    this.processToastQueue();
  }
  
  processToastQueue() {
    if (this.isShowingToast || this.toastQueue.length === 0) {
      return;
    }
    
    this.isShowingToast = true;
    const { message, type, duration } = this.toastQueue.shift();
    
    const container = document.getElementById('toast-container');
    if (!container) {
      this.isShowingToast = false;
      return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Add icon based on type
    const icons = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
      <i class="fas ${icons[type] || icons.info}"></i>
      <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after duration
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        toast.remove();
        this.isShowingToast = false;
        this.processToastQueue();
      }, 300);
    }, duration);
  }
  
  // Show loading overlay
  showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      const messageEl = overlay.querySelector('p');
      if (messageEl) {
        messageEl.textContent = message;
      }
      overlay.style.display = 'flex';
    }
  }
  
  // Hide loading overlay
  hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.style.display = 'none';
    }
  }
  
  // Generate unique ID
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
  
  // Deep clone object
  deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
      return obj;
    }
    
    if (obj instanceof Date) {
      return new Date(obj.getTime());
    }
    
    if (obj instanceof Array) {
      return obj.map(item => this.deepClone(item));
    }
    
    if (obj instanceof Object) {
      const clonedObj = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          clonedObj[key] = this.deepClone(obj[key]);
        }
      }
      return clonedObj;
    }
  }
  
  // Calculate distance between two coordinates
  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 3958.8; // Radius of Earth in miles
    const dLat = this.toRad(lat2 - lat1);
    const dLon = this.toRad(lon2 - lon1);
    
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(this.toRad(lat1)) * Math.cos(this.toRad(lat2)) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
              
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }
  
  toRad(deg) {
    return deg * (Math.PI/180);
  }
  
  // Format file size
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  // Get device info
  getDeviceInfo() {
    const userAgent = navigator.userAgent;
    
    return {
      isIOS: /iPad|iPhone|iPod/.test(userAgent) && !window.MSStream,
      isAndroid: /Android/.test(userAgent),
      isMobile: /Mobi|Android/i.test(userAgent),
      isTablet: /Tablet|iPad/i.test(userAgent),
      isSafari: /^((?!chrome|android).)*safari/i.test(userAgent),
      isChrome: /Chrome/.test(userAgent),
      isStandalone: window.matchMedia('(display-mode: standalone)').matches ||
                    window.navigator.standalone === true
    };
  }
  
  // Check if app is installed as PWA
  isPWAInstalled() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }
  
  // Vibrate device
  vibrate(pattern = [200]) {
    if ('vibrate' in navigator) {
      navigator.vibrate(pattern);
    }
  }
  
  // Copy to clipboard
  async copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        this.showToast('Copied to clipboard', 'success');
        return true;
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
          document.execCommand('copy');
          this.showToast('Copied to clipboard', 'success');
          return true;
        } catch (err) {
          this.showToast('Failed to copy', 'error');
          return false;
        } finally {
          document.body.removeChild(textArea);
        }
      }
    } catch (err) {
      this.showToast('Failed to copy', 'error');
      return false;
    }
  }
  
  // Request notification permission
  async requestNotificationPermission() {
    if (!('Notification' in window)) {
      return false;
    }
    
    if (Notification.permission === 'granted') {
      return true;
    }
    
    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    
    return false;
  }
  
  // Show notification
  async showNotification(title, options = {}) {
    const hasPermission = await this.requestNotificationPermission();
    
    if (!hasPermission) {
      return false;
    }
    
    const notification = new Notification(title, {
      icon: '/mobile_app/images/icons/icon-192x192.png',
      badge: '/mobile_app/images/icons/icon-72x72.png',
      ...options
    });
    
    notification.onclick = () => {
      window.focus();
      notification.close();
    };
    
    return true;
  }
  
  // Smooth scroll to element
  scrollToElement(element, offset = 0) {
    const y = element.getBoundingClientRect().top + window.pageYOffset + offset;
    
    window.scrollTo({
      top: y,
      behavior: 'smooth'
    });
  }
  
  // Check if element is in viewport
  isInViewport(element) {
    const rect = element.getBoundingClientRect();
    
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }
  
  // Get query parameters
  getQueryParams() {
    const params = {};
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    
    for (const [key, value] of urlParams.entries()) {
      params[key] = value;
    }
    
    return params;
  }
  
  // Set query parameter
  setQueryParam(key, value) {
    const url = new URL(window.location);
    url.searchParams.set(key, value);
    window.history.pushState({}, '', url);
  }
  
  // Remove query parameter
  removeQueryParam(key) {
    const url = new URL(window.location);
    url.searchParams.delete(key);
    window.history.pushState({}, '', url);
  }
  
  // Storage wrapper with JSON support
  storage = {
    get(key) {
      try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
      } catch (error) {
        return localStorage.getItem(key);
      }
    },
    
    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (error) {
        console.error('Storage error:', error);
      }
    },
    
    remove(key) {
      localStorage.removeItem(key);
    },
    
    clear() {
      localStorage.clear();
    }
  };
  
  // Session storage wrapper
  session = {
    get(key) {
      try {
        const item = sessionStorage.getItem(key);
        return item ? JSON.parse(item) : null;
      } catch (error) {
        return sessionStorage.getItem(key);
      }
    },
    
    set(key, value) {
      try {
        sessionStorage.setItem(key, JSON.stringify(value));
      } catch (error) {
        console.error('Session storage error:', error);
      }
    },
    
    remove(key) {
      sessionStorage.removeItem(key);
    },
    
    clear() {
      sessionStorage.clear();
    }
  };
}

// Create global utils instance
window.utils = new Utils();