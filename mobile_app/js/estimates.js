// Tree Service Estimator Pro - Estimates Module
class EstimatesService {
  constructor() {
    this.currentEstimate = null;
    this.estimateCache = new Map();
    this.defaultCrewRate = 75; // Per hour per person
    this.defaultTravelRate = 1.50; // Per mile
    this.emergencyMultiplier = 1.5;
    
    // Equipment rates (per hour)
    this.equipmentRates = {
      chipper: 125,
      bucket_truck: 150,
      crane: 200,
      stump_grinder: 100
    };
  }
  
  async calculateEstimate(data) {
    // Extract data
    const {
      work_hours,
      crew_size,
      equipment = [],
      emergency_service = false,
      service_address,
      latitude,
      longitude
    } = data;
    
    // Calculate travel distance (mock calculation)
    const travelMiles = await this.calculateTravelDistance(latitude, longitude, service_address);
    const travelTime = Math.ceil(travelMiles * 2); // Rough estimate: 2 min per mile
    
    // Calculate costs
    let laborCost = work_hours * crew_size * this.defaultCrewRate;
    
    // Equipment costs
    let equipmentCost = 0;
    equipment.forEach(item => {
      const rate = this.equipmentRates[item] || 0;
      equipmentCost += rate * work_hours;
    });
    
    // Travel costs
    const travelCost = (travelMiles * this.defaultTravelRate * 2) + // Round trip mileage
                      (travelTime / 60 * this.defaultCrewRate * 2); // Travel time labor
    
    // Apply emergency multiplier
    if (emergency_service) {
      laborCost *= this.emergencyMultiplier;
    }
    
    // Calculate totals
    const subtotal = laborCost + equipmentCost + travelCost;
    const overhead = subtotal * 0.25; // 25% overhead
    const profit = subtotal * 0.35; // 35% profit margin
    const totalAmount = this.roundToNearest5(subtotal + overhead + profit);
    
    // Create calculation object
    const calculation = {
      labor_cost: this.roundToNearest5(laborCost),
      equipment_cost: this.roundToNearest5(equipmentCost),
      travel_cost: this.roundToNearest5(travelCost),
      subtotal: this.roundToNearest5(subtotal),
      overhead: this.roundToNearest5(overhead),
      profit: this.roundToNearest5(profit),
      total_amount: totalAmount,
      breakdown: {
        hours: work_hours,
        crew_size: crew_size,
        crew_rate: this.defaultCrewRate,
        equipment_items: equipment,
        travel_miles: travelMiles,
        travel_time: travelTime,
        emergency_service: emergency_service
      }
    };
    
    // Try to get server calculation for validation
    if (navigator.onLine) {
      try {
        const serverCalc = await api.calculateEstimate({
          ...data,
          travel_miles: travelMiles,
          travel_time_minutes: travelTime
        });
        
        // Use server calculation if available
        return serverCalc;
      } catch (error) {
        console.warn('Server calculation failed, using local calculation:', error);
      }
    }
    
    return calculation;
  }
  
  async calculateTravelDistance(lat, lng, address) {
    // In production, this would use a real distance API
    // For now, return a mock distance based on coordinates
    if (lat && lng) {
      // Mock office location
      const officeLat = 40.7128;
      const officeLng = -74.0060;
      
      // Simple distance calculation
      const distance = this.haversineDistance(officeLat, officeLng, lat, lng);
      return Math.round(distance);
    }
    
    // Default distance if no coordinates
    return 10;
  }
  
  haversineDistance(lat1, lon1, lat2, lon2) {
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
  
  roundToNearest5(amount) {
    return Math.round(amount / 5) * 5;
  }
  
  async saveEstimate(estimateData) {
    // Prepare estimate object
    const estimate = {
      customer_name: estimateData.customer_name,
      customer_phone: estimateData.customer_phone,
      customer_email: estimateData.customer_email || null,
      service_address: estimateData.service_address,
      latitude: estimateData.latitude || null,
      longitude: estimateData.longitude || null,
      job_type: estimateData.job_type,
      description: estimateData.job_description,
      estimated_hours: estimateData.work_hours,
      crew_size: estimateData.crew_size,
      equipment: estimateData.equipment || [],
      emergency_service: estimateData.emergency_service || false,
      photos: estimateData.photos || [],
      calculation: estimateData.calculation,
      status: 'Draft',
      created_by: auth.currentUser.id
    };
    
    try {
      // Try to save online
      const result = await api.createEstimate(estimate);
      
      // Cache the estimate
      this.estimateCache.set(result.id, result);
      
      // Store in offline storage too
      await offline.saveEstimate(result);
      
      return {
        success: true,
        estimate: result
      };
      
    } catch (error) {
      console.error('Failed to save estimate online:', error);
      
      // If offline, save locally
      if (!navigator.onLine) {
        return await this.saveOfflineEstimate(estimate);
      }
      
      throw error;
    }
  }
  
  async saveOfflineEstimate(estimate) {
    try {
      // Generate temporary ID
      estimate.id = `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      estimate.estimate_number = `TEMP-${Date.now()}`;
      estimate.created_at = new Date().toISOString();
      estimate.updated_at = new Date().toISOString();
      estimate.is_offline = true;
      
      // Save to offline storage
      await offline.saveEstimate(estimate);
      
      // Add to pending sync queue
      await offline.addPendingSync({
        type: 'estimate',
        action: 'create',
        data: estimate,
        timestamp: Date.now()
      });
      
      // Register background sync
      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-estimates');
      }
      
      return {
        success: true,
        estimate: estimate
      };
      
    } catch (error) {
      console.error('Failed to save offline estimate:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
  
  async getEstimate(id) {
    // Check cache first
    if (this.estimateCache.has(id)) {
      return this.estimateCache.get(id);
    }
    
    try {
      // Try to fetch from server
      const estimate = await api.getEstimate(id);
      
      // Cache it
      this.estimateCache.set(id, estimate);
      
      // Update offline storage
      await offline.saveEstimate(estimate);
      
      return estimate;
      
    } catch (error) {
      // Try offline storage
      const offlineEstimate = await offline.getEstimate(id);
      if (offlineEstimate) {
        return offlineEstimate;
      }
      
      throw error;
    }
  }
  
  async updateEstimate(id, updates) {
    try {
      // Update online
      const updated = await api.updateEstimate(id, updates);
      
      // Update cache
      this.estimateCache.set(id, updated);
      
      // Update offline storage
      await offline.saveEstimate(updated);
      
      return updated;
      
    } catch (error) {
      if (!navigator.onLine) {
        // Save update for later sync
        const estimate = await this.getEstimate(id);
        const updatedEstimate = { ...estimate, ...updates, updated_at: new Date().toISOString() };
        
        await offline.saveEstimate(updatedEstimate);
        await offline.addPendingSync({
          type: 'estimate',
          action: 'update',
          id: id,
          data: updates,
          timestamp: Date.now()
        });
        
        return updatedEstimate;
      }
      
      throw error;
    }
  }
  
  async deleteEstimate(id) {
    try {
      await api.deleteEstimate(id);
      
      // Remove from cache
      this.estimateCache.delete(id);
      
      // Remove from offline storage
      await offline.deleteEstimate(id);
      
      return true;
      
    } catch (error) {
      if (!navigator.onLine) {
        // Mark for deletion on sync
        await offline.addPendingSync({
          type: 'estimate',
          action: 'delete',
          id: id,
          timestamp: Date.now()
        });
        
        // Remove locally
        await offline.deleteEstimate(id);
        
        return true;
      }
      
      throw error;
    }
  }
  
  async approveEstimate(id, notes = '') {
    if (!auth.hasRole('Manager')) {
      throw new Error('Insufficient permissions to approve estimates');
    }
    
    try {
      const result = await api.approveEstimate(id, notes);
      
      // Update cache
      if (this.estimateCache.has(id)) {
        const estimate = this.estimateCache.get(id);
        estimate.status = 'Approved';
        estimate.approved_by = auth.currentUser.id;
        estimate.approved_at = new Date().toISOString();
      }
      
      return result;
      
    } catch (error) {
      if (!navigator.onLine) {
        // Queue for later
        await offline.addPendingSync({
          type: 'estimate',
          action: 'approve',
          id: id,
          data: { notes },
          timestamp: Date.now()
        });
        
        utils.showToast('Approval queued for sync', 'warning');
        return { success: true, queued: true };
      }
      
      throw error;
    }
  }
  
  async exportEstimate(id, format = 'pdf') {
    const estimate = await this.getEstimate(id);
    
    if (format === 'pdf') {
      // Generate PDF (would use a library like jsPDF in production)
      window.print();
    } else if (format === 'json') {
      // Export as JSON
      const blob = new Blob([JSON.stringify(estimate, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `estimate_${estimate.estimate_number}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }
  
  async emailEstimate(id, email) {
    try {
      return await api.sendEstimate(id, email);
    } catch (error) {
      if (!navigator.onLine) {
        // Queue for later
        await offline.addPendingSync({
          type: 'estimate',
          action: 'email',
          id: id,
          data: { email },
          timestamp: Date.now()
        });
        
        utils.showToast('Email queued for sending when online', 'warning');
        return { success: true, queued: true };
      }
      
      throw error;
    }
  }
  
  formatEstimateForDisplay(estimate) {
    return {
      ...estimate,
      displayNumber: estimate.estimate_number || estimate.id.substr(0, 8),
      displayStatus: this.getStatusDisplay(estimate.status),
      displayDate: utils.formatDate(estimate.created_at),
      displayTotal: utils.formatCurrency(estimate.calculation?.total_amount || 0),
      statusClass: `status-${estimate.status.toLowerCase()}`,
      jobTypeDisplay: this.getJobTypeDisplay(estimate.job_type)
    };
  }
  
  getStatusDisplay(status) {
    const statusMap = {
      'Draft': 'Draft',
      'Pending': 'Pending Approval',
      'Approved': 'Approved',
      'Rejected': 'Rejected',
      'Sent': 'Sent to Customer',
      'Accepted': 'Accepted',
      'Completed': 'Completed'
    };
    
    return statusMap[status] || status;
  }
  
  getJobTypeDisplay(jobType) {
    const typeMap = {
      'tree-removal': 'Tree Removal',
      'tree-trimming': 'Tree Trimming',
      'stump-grinding': 'Stump Grinding',
      'emergency': 'Emergency Service',
      'other': 'Other Service'
    };
    
    return typeMap[jobType] || jobType;
  }
  
  async searchEstimates(query) {
    const allEstimates = await offline.getAllEstimates();
    
    const searchLower = query.toLowerCase();
    
    return allEstimates.filter(estimate => {
      return estimate.customer_name.toLowerCase().includes(searchLower) ||
             estimate.service_address.toLowerCase().includes(searchLower) ||
             estimate.estimate_number.toLowerCase().includes(searchLower) ||
             estimate.description.toLowerCase().includes(searchLower);
    });
  }
  
  async filterEstimates(filter) {
    const allEstimates = await offline.getAllEstimates();
    
    if (filter === 'all') {
      return allEstimates;
    }
    
    return allEstimates.filter(estimate => {
      return estimate.status.toLowerCase() === filter.toLowerCase();
    });
  }
}

// Create global estimates service instance
window.estimates = new EstimatesService();