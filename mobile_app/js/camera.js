// Tree Service Estimator Pro - Camera Module
class CameraService {
  constructor() {
    this.photos = [];
    this.maxPhotos = 10;
    this.maxFileSize = 10 * 1024 * 1024; // 10MB
    this.acceptedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    
    this.setupEventListeners();
  }
  
  setupEventListeners() {
    // File input change handler
    const photoInput = document.getElementById('photo-input');
    if (photoInput) {
      photoInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }
  }
  
  async capturePhoto() {
    const photoInput = document.getElementById('photo-input');
    if (!photoInput) return;
    
    // Set capture attribute for camera
    photoInput.setAttribute('capture', 'camera');
    photoInput.click();
  }
  
  async selectPhoto() {
    const photoInput = document.getElementById('photo-input');
    if (!photoInput) return;
    
    // Remove capture attribute for gallery
    photoInput.removeAttribute('capture');
    photoInput.click();
  }
  
  async handleFileSelect(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    for (const file of files) {
      await this.processPhoto(file);
    }
    
    // Clear input for next selection
    event.target.value = '';
  }
  
  async processPhoto(file) {
    // Validate file
    if (!this.validatePhoto(file)) {
      return;
    }
    
    // Check photo limit
    if (app.photos.length >= this.maxPhotos) {
      utils.showToast(`Maximum ${this.maxPhotos} photos allowed`, 'warning');
      return;
    }
    
    try {
      // Compress image if needed
      const processedFile = await this.compressImage(file);
      
      // Create preview
      const preview = await this.createPreview(processedFile);
      
      // Add to photos array
      const photoData = {
        id: Date.now() + Math.random(),
        file: processedFile,
        preview: preview,
        name: file.name,
        size: processedFile.size,
        type: processedFile.type,
        timestamp: new Date().toISOString()
      };
      
      app.photos.push(photoData);
      
      // Display preview
      this.displayPhotoPreview(photoData);
      
      // Store in offline storage if needed
      if (!navigator.onLine) {
        await this.storePhotoOffline(photoData);
      }
      
    } catch (error) {
      console.error('Photo processing error:', error);
      utils.showToast('Failed to process photo', 'error');
    }
  }
  
  validatePhoto(file) {
    // Check file type
    if (!this.acceptedTypes.includes(file.type)) {
      utils.showToast('Please select a valid image file (JPEG, PNG, WebP)', 'error');
      return false;
    }
    
    // Check file size
    if (file.size > this.maxFileSize) {
      utils.showToast(`Photo size must be less than ${this.maxFileSize / 1024 / 1024}MB`, 'error');
      return false;
    }
    
    return true;
  }
  
  async compressImage(file) {
    // Skip compression for small files
    if (file.size < 1024 * 1024) { // Less than 1MB
      return file;
    }
    
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const img = new Image();
        
        img.onload = () => {
          // Calculate new dimensions
          let { width, height } = img;
          const maxDimension = 1920;
          
          if (width > maxDimension || height > maxDimension) {
            if (width > height) {
              height = (height / width) * maxDimension;
              width = maxDimension;
            } else {
              width = (width / height) * maxDimension;
              height = maxDimension;
            }
          }
          
          // Create canvas
          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);
          
          // Convert to blob
          canvas.toBlob((blob) => {
            if (blob) {
              // Create new file from blob
              const compressedFile = new File([blob], file.name, {
                type: 'image/jpeg',
                lastModified: Date.now()
              });
              resolve(compressedFile);
            } else {
              reject(new Error('Compression failed'));
            }
          }, 'image/jpeg', 0.85); // 85% quality
        };
        
        img.onerror = () => reject(new Error('Image load failed'));
        img.src = e.target.result;
      };
      
      reader.onerror = () => reject(new Error('File read failed'));
      reader.readAsDataURL(file);
    });
  }
  
  async createPreview(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        resolve(e.target.result);
      };
      
      reader.onerror = () => reject(new Error('Preview creation failed'));
      reader.readAsDataURL(file);
    });
  }
  
  displayPhotoPreview(photoData) {
    const container = document.getElementById('photo-preview');
    if (!container) return;
    
    const photoEl = document.createElement('div');
    photoEl.className = 'photo-item';
    photoEl.innerHTML = `
      <img src="${photoData.preview}" alt="${photoData.name}" />
      <button class="photo-remove" onclick="camera.removePhoto('${photoData.id}')">
        <i class="fas fa-times"></i>
      </button>
    `;
    
    container.appendChild(photoEl);
  }
  
  removePhoto(photoId) {
    // Remove from array
    const index = app.photos.findIndex(p => p.id == photoId);
    if (index > -1) {
      app.photos.splice(index, 1);
    }
    
    // Remove from display
    const container = document.getElementById('photo-preview');
    if (container) {
      container.innerHTML = '';
      app.photos.forEach(photo => this.displayPhotoPreview(photo));
    }
    
    // Remove from offline storage
    this.removePhotoOffline(photoId);
  }
  
  async storePhotoOffline(photoData) {
    try {
      const db = await offline.openDB();
      const transaction = db.transaction(['photos'], 'readwrite');
      const store = transaction.objectStore('photos');
      
      await store.put({
        id: photoData.id,
        estimateId: null, // Will be updated when estimate is saved
        preview: photoData.preview,
        name: photoData.name,
        size: photoData.size,
        type: photoData.type,
        timestamp: photoData.timestamp
      });
      
    } catch (error) {
      console.error('Failed to store photo offline:', error);
    }
  }
  
  async removePhotoOffline(photoId) {
    try {
      const db = await offline.openDB();
      const transaction = db.transaction(['photos'], 'readwrite');
      const store = transaction.objectStore('photos');
      
      await store.delete(photoId);
      
    } catch (error) {
      console.error('Failed to remove photo from offline storage:', error);
    }
  }
  
  async uploadPhotos(photos, estimateId) {
    const uploadedPhotos = [];
    
    for (const photo of photos) {
      try {
        if (navigator.onLine) {
          // Upload to server
          const result = await api.uploadPhoto(photo.file, estimateId);
          uploadedPhotos.push({
            ...photo,
            url: result.url,
            uploaded: true
          });
        } else {
          // Mark for later upload
          uploadedPhotos.push({
            ...photo,
            uploaded: false,
            pendingUpload: true
          });
        }
      } catch (error) {
        console.error('Photo upload failed:', error);
        uploadedPhotos.push({
          ...photo,
          uploaded: false,
          error: error.message
        });
      }
    }
    
    return uploadedPhotos;
  }
  
  async getPhotoFromCamera() {
    // Check if camera API is available
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      utils.showToast('Camera not available on this device', 'error');
      return null;
    }
    
    try {
      // Request camera permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      
      // Create video element
      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();
      
      // Wait for video to be ready
      await new Promise(resolve => {
        video.onloadedmetadata = resolve;
      });
      
      // Create canvas and capture image
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      // Stop camera stream
      stream.getTracks().forEach(track => track.stop());
      
      // Convert to blob
      return new Promise((resolve) => {
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `photo_${Date.now()}.jpg`, {
              type: 'image/jpeg',
              lastModified: Date.now()
            });
            resolve(file);
          } else {
            resolve(null);
          }
        }, 'image/jpeg', 0.85);
      });
      
    } catch (error) {
      console.error('Camera access error:', error);
      
      if (error.name === 'NotAllowedError') {
        utils.showToast('Camera permission denied', 'error');
      } else {
        utils.showToast('Failed to access camera', 'error');
      }
      
      return null;
    }
  }
  
  // EXIF data extraction for GPS coordinates
  async extractGPSFromPhoto(file) {
    // This would use a library like exif-js in production
    // For now, return null
    return null;
  }
  
  // Generate thumbnail for faster preview
  async generateThumbnail(file, maxSize = 200) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const img = new Image();
        
        img.onload = () => {
          // Calculate thumbnail dimensions
          let { width, height } = img;
          
          if (width > height) {
            height = (height / width) * maxSize;
            width = maxSize;
          } else {
            width = (width / height) * maxSize;
            height = maxSize;
          }
          
          // Create canvas
          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);
          
          // Return data URL
          resolve(canvas.toDataURL('image/jpeg', 0.7));
        };
        
        img.onerror = () => reject(new Error('Thumbnail generation failed'));
        img.src = e.target.result;
      };
      
      reader.onerror = () => reject(new Error('File read failed'));
      reader.readAsDataURL(file);
    });
  }
}

// Create global camera service instance
window.camera = new CameraService();