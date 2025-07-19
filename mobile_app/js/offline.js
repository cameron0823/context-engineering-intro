// Tree Service Estimator Pro - Offline Storage Module
class OfflineStorage {
  constructor() {
    this.dbName = 'TreeServiceDB';
    this.dbVersion = 1;
    this.db = null;
    this.syncQueue = [];
    this.lastSync = null;
  }
  
  async init() {
    try {
      this.db = await this.openDB();
      await this.loadSyncQueue();
      await this.checkSyncStatus();
      
      // Listen for online/offline events
      window.addEventListener('online', () => this.handleOnline());
      window.addEventListener('offline', () => this.handleOffline());
      
      // Listen for sync messages from service worker
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('message', (event) => {
          this.handleServiceWorkerMessage(event);
        });
      }
      
      console.log('Offline storage initialized');
    } catch (error) {
      console.error('Failed to initialize offline storage:', error);
    }
  }
  
  openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onerror = () => {
        reject(new Error('Failed to open database'));
      };
      
      request.onsuccess = (event) => {
        resolve(event.target.result);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores
        if (!db.objectStoreNames.contains('estimates')) {
          const estimatesStore = db.createObjectStore('estimates', { keyPath: 'id' });
          estimatesStore.createIndex('status', 'status', { unique: false });
          estimatesStore.createIndex('created_at', 'created_at', { unique: false });
          estimatesStore.createIndex('customer_name', 'customer_name', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('pendingSync')) {
          const syncStore = db.createObjectStore('pendingSync', { keyPath: 'id', autoIncrement: true });
          syncStore.createIndex('timestamp', 'timestamp', { unique: false });
          syncStore.createIndex('type', 'type', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('photos')) {
          const photosStore = db.createObjectStore('photos', { keyPath: 'id' });
          photosStore.createIndex('estimateId', 'estimateId', { unique: false });
        }
        
        if (!db.objectStoreNames.contains('offlineAuth')) {
          db.createObjectStore('offlineAuth', { keyPath: 'username' });
        }
        
        if (!db.objectStoreNames.contains('dashboardCache')) {
          db.createObjectStore('dashboardCache', { keyPath: 'key' });
        }
        
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
      };
    });
  }
  
  async saveEstimate(estimate) {
    const transaction = this.db.transaction(['estimates'], 'readwrite');
    const store = transaction.objectStore('estimates');
    
    return new Promise((resolve, reject) => {
      const request = store.put(estimate);
      
      request.onsuccess = () => resolve(estimate);
      request.onerror = () => reject(new Error('Failed to save estimate'));
    });
  }
  
  async getEstimate(id) {
    const transaction = this.db.transaction(['estimates'], 'readonly');
    const store = transaction.objectStore('estimates');
    
    return new Promise((resolve, reject) => {
      const request = store.get(id);
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to get estimate'));
    });
  }
  
  async getAllEstimates() {
    const transaction = this.db.transaction(['estimates'], 'readonly');
    const store = transaction.objectStore('estimates');
    
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      
      request.onsuccess = () => {
        const estimates = request.result || [];
        // Sort by created_at descending
        estimates.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        resolve(estimates);
      };
      
      request.onerror = () => reject(new Error('Failed to get estimates'));
    });
  }
  
  async getEstimates(filter = {}) {
    const transaction = this.db.transaction(['estimates'], 'readonly');
    const store = transaction.objectStore('estimates');
    
    return new Promise((resolve, reject) => {
      let request;
      
      if (filter.status) {
        const index = store.index('status');
        request = index.getAll(filter.status);
      } else if (filter.dateRange) {
        const index = store.index('created_at');
        const range = IDBKeyRange.bound(filter.dateRange.start, filter.dateRange.end);
        request = index.getAll(range);
      } else {
        request = store.getAll();
      }
      
      request.onsuccess = () => {
        let estimates = request.result || [];
        
        // Apply additional filters
        if (filter.search) {
          const searchLower = filter.search.toLowerCase();
          estimates = estimates.filter(est => 
            est.customer_name.toLowerCase().includes(searchLower) ||
            est.service_address.toLowerCase().includes(searchLower) ||
            est.estimate_number.toLowerCase().includes(searchLower)
          );
        }
        
        // Sort
        estimates.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        resolve(estimates);
      };
      
      request.onerror = () => reject(new Error('Failed to get estimates'));
    });
  }
  
  async deleteEstimate(id) {
    const transaction = this.db.transaction(['estimates'], 'readwrite');
    const store = transaction.objectStore('estimates');
    
    return new Promise((resolve, reject) => {
      const request = store.delete(id);
      
      request.onsuccess = () => resolve(true);
      request.onerror = () => reject(new Error('Failed to delete estimate'));
    });
  }
  
  async addPendingSync(syncData) {
    const transaction = this.db.transaction(['pendingSync'], 'readwrite');
    const store = transaction.objectStore('pendingSync');
    
    // Add user token for authentication
    syncData.token = auth.getToken();
    
    return new Promise((resolve, reject) => {
      const request = store.add(syncData);
      
      request.onsuccess = () => {
        this.syncQueue.push({ ...syncData, id: request.result });
        resolve(request.result);
      };
      
      request.onerror = () => reject(new Error('Failed to add to sync queue'));
    });
  }
  
  async loadSyncQueue() {
    const transaction = this.db.transaction(['pendingSync'], 'readonly');
    const store = transaction.objectStore('pendingSync');
    
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      
      request.onsuccess = () => {
        this.syncQueue = request.result || [];
        resolve(this.syncQueue);
      };
      
      request.onerror = () => reject(new Error('Failed to load sync queue'));
    });
  }
  
  async removePendingSync(id) {
    const transaction = this.db.transaction(['pendingSync'], 'readwrite');
    const store = transaction.objectStore('pendingSync');
    
    return new Promise((resolve, reject) => {
      const request = store.delete(id);
      
      request.onsuccess = () => {
        this.syncQueue = this.syncQueue.filter(item => item.id !== id);
        resolve(true);
      };
      
      request.onerror = () => reject(new Error('Failed to remove from sync queue'));
    });
  }
  
  async syncPendingData() {
    if (!navigator.onLine || this.syncQueue.length === 0) {
      return;
    }
    
    console.log(`Syncing ${this.syncQueue.length} pending items...`);
    utils.showToast('Syncing offline data...', 'info');
    
    const results = {
      success: 0,
      failed: 0,
      errors: []
    };
    
    for (const item of this.syncQueue) {
      try {
        await this.syncItem(item);
        await this.removePendingSync(item.id);
        results.success++;
      } catch (error) {
        console.error('Sync failed for item:', item, error);
        results.failed++;
        results.errors.push({ item, error: error.message });
      }
    }
    
    // Update last sync time
    this.lastSync = new Date().toISOString();
    await this.saveSetting('lastSync', this.lastSync);
    
    // Show results
    if (results.success > 0) {
      utils.showToast(`Synced ${results.success} items successfully`, 'success');
    }
    
    if (results.failed > 0) {
      utils.showToast(`Failed to sync ${results.failed} items`, 'error');
    }
    
    return results;
  }
  
  async syncItem(item) {
    switch (item.type) {
      case 'estimate':
        return this.syncEstimate(item);
      case 'photo':
        return this.syncPhoto(item);
      default:
        throw new Error(`Unknown sync type: ${item.type}`);
    }
  }
  
  async syncEstimate(item) {
    switch (item.action) {
      case 'create':
        // Remove temporary ID before sending
        const estimateData = { ...item.data };
        delete estimateData.id;
        delete estimateData.estimate_number;
        delete estimateData.is_offline;
        
        const created = await api.createEstimate(estimateData);
        
        // Update local estimate with server data
        await this.deleteEstimate(item.data.id);
        await this.saveEstimate(created);
        
        return created;
        
      case 'update':
        return await api.updateEstimate(item.id, item.data);
        
      case 'delete':
        return await api.deleteEstimate(item.id);
        
      case 'approve':
        return await api.approveEstimate(item.id, item.data.notes);
        
      case 'email':
        return await api.sendEstimate(item.id, item.data.email);
        
      default:
        throw new Error(`Unknown estimate action: ${item.action}`);
    }
  }
  
  async syncPhoto(item) {
    // Get photo data
    const photo = await this.getPhoto(item.photoId);
    if (!photo) {
      throw new Error('Photo not found');
    }
    
    // Convert base64 to blob
    const blob = await this.base64ToBlob(photo.preview, photo.type);
    const file = new File([blob], photo.name, { type: photo.type });
    
    // Upload photo
    return await api.uploadPhoto(file, item.estimateId);
  }
  
  async base64ToBlob(base64, type) {
    const base64Data = base64.split(',')[1];
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type });
  }
  
  async getPhoto(id) {
    const transaction = this.db.transaction(['photos'], 'readonly');
    const store = transaction.objectStore('photos');
    
    return new Promise((resolve, reject) => {
      const request = store.get(id);
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to get photo'));
    });
  }
  
  async getDashboardData() {
    const transaction = this.db.transaction(['dashboardCache'], 'readonly');
    const store = transaction.objectStore('dashboardCache');
    
    return new Promise((resolve, reject) => {
      const request = store.get('dashboard');
      
      request.onsuccess = () => {
        const data = request.result;
        if (data && data.timestamp) {
          // Check if cache is not too old (1 hour)
          const age = Date.now() - data.timestamp;
          if (age < 60 * 60 * 1000) {
            resolve(data.value);
            return;
          }
        }
        resolve(null);
      };
      
      request.onerror = () => reject(new Error('Failed to get dashboard cache'));
    });
  }
  
  async saveDashboardData(data) {
    const transaction = this.db.transaction(['dashboardCache'], 'readwrite');
    const store = transaction.objectStore('dashboardCache');
    
    return new Promise((resolve, reject) => {
      const request = store.put({
        key: 'dashboard',
        value: data,
        timestamp: Date.now()
      });
      
      request.onsuccess = () => resolve(true);
      request.onerror = () => reject(new Error('Failed to save dashboard cache'));
    });
  }
  
  async saveSetting(key, value) {
    const transaction = this.db.transaction(['settings'], 'readwrite');
    const store = transaction.objectStore('settings');
    
    return new Promise((resolve, reject) => {
      const request = store.put({ key, value });
      
      request.onsuccess = () => resolve(true);
      request.onerror = () => reject(new Error('Failed to save setting'));
    });
  }
  
  async getSetting(key) {
    const transaction = this.db.transaction(['settings'], 'readonly');
    const store = transaction.objectStore('settings');
    
    return new Promise((resolve, reject) => {
      const request = store.get(key);
      
      request.onsuccess = () => {
        const result = request.result;
        resolve(result ? result.value : null);
      };
      
      request.onerror = () => reject(new Error('Failed to get setting'));
    });
  }
  
  async clearOfflineAuth() {
    const transaction = this.db.transaction(['offlineAuth'], 'readwrite');
    const store = transaction.objectStore('offlineAuth');
    
    return new Promise((resolve, reject) => {
      const request = store.clear();
      
      request.onsuccess = () => resolve(true);
      request.onerror = () => reject(new Error('Failed to clear offline auth'));
    });
  }
  
  async checkSyncStatus() {
    this.lastSync = await this.getSetting('lastSync');
    
    // Check if we have pending items
    if (this.syncQueue.length > 0 && navigator.onLine) {
      // Try to sync
      setTimeout(() => this.syncPendingData(), 5000);
    }
  }
  
  handleOnline() {
    console.log('App is online, checking for pending sync...');
    this.syncPendingData();
  }
  
  handleOffline() {
    console.log('App is offline, data will be synced when connection returns');
  }
  
  handleServiceWorkerMessage(event) {
    if (event.data && event.data.type === 'estimate-synced') {
      // Update local estimate with server ID
      const { localId, serverId } = event.data.data;
      this.updateEstimateId(localId, serverId);
    }
  }
  
  async updateEstimateId(oldId, newId) {
    const estimate = await this.getEstimate(oldId);
    if (estimate) {
      estimate.id = newId;
      await this.saveEstimate(estimate);
      await this.deleteEstimate(oldId);
    }
  }
  
  async clearAllData() {
    const stores = ['estimates', 'pendingSync', 'photos', 'dashboardCache', 'settings'];
    
    for (const storeName of stores) {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      await new Promise((resolve, reject) => {
        const request = store.clear();
        request.onsuccess = () => resolve();
        request.onerror = () => reject(new Error(`Failed to clear ${storeName}`));
      });
    }
    
    this.syncQueue = [];
    this.lastSync = null;
  }
  
  async exportData() {
    const data = {
      estimates: await this.getAllEstimates(),
      pendingSync: this.syncQueue,
      settings: {
        lastSync: this.lastSync
      },
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tree-service-backup-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  
  async importData(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        try {
          const data = JSON.parse(e.target.result);
          
          // Import estimates
          if (data.estimates) {
            for (const estimate of data.estimates) {
              await this.saveEstimate(estimate);
            }
          }
          
          // Import pending sync
          if (data.pendingSync) {
            for (const item of data.pendingSync) {
              await this.addPendingSync(item);
            }
          }
          
          utils.showToast('Data imported successfully', 'success');
          resolve(true);
          
        } catch (error) {
          console.error('Import failed:', error);
          utils.showToast('Failed to import data', 'error');
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }
}

// Create global offline storage instance
window.offline = new OfflineStorage();