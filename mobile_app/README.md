# Tree Service Estimator Pro - Mobile PWA

A complete Progressive Web App (PWA) for field teams to create estimates on mobile devices with offline support.

## Features

### Core Functionality
- ✅ Complete estimate creation wizard
- ✅ Offline-first architecture with service worker
- ✅ Camera integration for job photos
- ✅ GPS location services
- ✅ Real-time pricing calculations
- ✅ Background sync when online

### Mobile Optimizations
- ✅ iPhone home screen installation
- ✅ Touch-optimized interface (44px+ targets)
- ✅ iOS safe area handling
- ✅ Responsive design for all screen sizes
- ✅ Dark mode support
- ✅ Offline mode indicators

### Technical Features
- ✅ JWT authentication with offline fallback
- ✅ IndexedDB for local storage
- ✅ Service worker caching strategies
- ✅ Background sync for offline estimates
- ✅ Push notification support
- ✅ Photo compression and optimization

## Quick Start

### Development Setup

1. **Ensure the backend is running:**
   ```bash
   cd ..
   python -m uvicorn src.main:app --reload --port 8002
   ```

2. **Serve the mobile app:**
   ```bash
   # Using Python's built-in server
   python -m http.server 8080 --directory mobile_app

   # Or using Node.js http-server
   npx http-server mobile_app -p 8080
   ```

3. **Access on mobile device:**
   - Find your computer's IP address
   - On mobile, navigate to: `http://YOUR_IP:8080`
   - Or use ngrok for secure tunnel: `ngrok http 8080`

### Installation on iPhone

1. Open Safari on iPhone
2. Navigate to the app URL
3. Tap Share button
4. Select "Add to Home Screen"
5. Name it "Tree Service Pro"
6. Tap "Add"

The app will now work offline from your home screen!

## File Structure

```
mobile_app/
├── index.html          # Main app shell
├── manifest.json       # PWA configuration
├── service-worker.js   # Offline functionality
├── offline.html        # Offline fallback page
├── css/
│   ├── styles.css      # Main styles
│   └── mobile.css      # Mobile-specific styles
├── js/
│   ├── app.js          # Main application logic
│   ├── auth.js         # Authentication service
│   ├── api.js          # API communication
│   ├── estimates.js    # Estimate management
│   ├── camera.js       # Camera integration
│   ├── offline.js      # Offline storage
│   └── utils.js        # Utility functions
└── images/
    └── icons/          # PWA icons (to be added)
```

## API Integration

The mobile app connects to the FastAPI backend at:
- Development: `http://localhost:8002/api`
- Production: `/api` (relative)

### Authentication Flow
1. User logs in with username/password
2. Receives JWT access token
3. Token stored in localStorage/sessionStorage
4. Offline credentials cached (hashed) for offline login

### Offline Sync
1. Estimates created offline get temporary IDs
2. Stored in IndexedDB with pending sync flag
3. Background sync triggered when online
4. Server IDs replace temporary IDs after sync

## Key Technologies

- **Service Worker**: Enables offline functionality and background sync
- **IndexedDB**: Client-side database for offline storage
- **Cache API**: Static asset caching for performance
- **Web App Manifest**: PWA installation and appearance
- **Geolocation API**: GPS coordinates for addresses
- **Camera API**: Photo capture through file input
- **Web Share API**: Native sharing capabilities

## Testing Checklist

### PWA Installation
- [ ] App installs from Safari "Add to Home Screen"
- [ ] App launches in standalone mode
- [ ] Splash screen displays during launch
- [ ] Status bar styling is correct

### Offline Functionality
- [ ] App loads when offline
- [ ] Can create estimates offline
- [ ] Photos are stored locally
- [ ] Sync occurs when back online

### Authentication
- [ ] Login works online
- [ ] Offline login works after online login
- [ ] Token refresh works properly
- [ ] Logout clears all credentials

### Estimate Creation
- [ ] All wizard steps work
- [ ] Validation prevents bad data
- [ ] Photos can be captured/selected
- [ ] GPS location works
- [ ] Calculations are accurate

### Performance
- [ ] Initial load < 3 seconds on 3G
- [ ] Smooth scrolling (60fps)
- [ ] Touch responses < 100ms
- [ ] Images load progressively

## Deployment

### Production Build Steps

1. **Update API endpoint in api.js:**
   ```javascript
   this.baseUrl = 'https://your-api-domain.com/api';
   ```

2. **Generate app icons:**
   - Create icons in sizes: 72, 96, 128, 144, 152, 192, 384, 512px
   - Save in `images/icons/` directory
   - Update `manifest.json` if paths change

3. **Configure HTTPS:**
   - PWA features require HTTPS in production
   - Service worker won't register on HTTP (except localhost)

4. **Deploy files:**
   - Upload all mobile_app files to web server
   - Ensure proper MIME types for manifest.json
   - Configure CORS on API server

5. **Test thoroughly:**
   - Test on real devices
   - Test offline scenarios
   - Verify background sync
   - Check performance metrics

### Environment Variables

No environment variables needed in the PWA itself. API endpoint is configured in `api.js`.

## Security Considerations

1. **Authentication**:
   - JWT tokens expire after 30 minutes
   - Refresh tokens should be used for extended sessions
   - Offline passwords are hashed with SHA-256

2. **Data Storage**:
   - Sensitive data in IndexedDB is not encrypted
   - Consider encryption for highly sensitive data
   - Clear storage on logout

3. **API Communication**:
   - Always use HTTPS in production
   - Implement certificate pinning for extra security
   - Validate all server responses

## Troubleshooting

### Service Worker Issues
- Check browser DevTools > Application > Service Workers
- Look for registration errors in console
- Ensure HTTPS in production
- Clear cache and re-register

### iOS Specific Issues
- Status bar overlaps: Check safe-area-inset-top
- Keyboard covers input: Implement keyboard avoidance
- Rubber band scrolling: Use -webkit-overflow-scrolling

### Sync Issues
- Check IndexedDB for pending items
- Verify network requests in DevTools
- Check service worker sync events
- Look for console errors

## Future Enhancements

1. **Biometric Authentication**: Touch ID/Face ID support
2. **Signature Capture**: Customer signature on estimates
3. **Route Optimization**: Multiple estimates routing
4. **Voice Notes**: Audio recordings for job details
5. **AR Measurements**: Camera-based measurements
6. **Team Collaboration**: Real-time estimate sharing
7. **Advanced Offline**: Conflict resolution strategies
8. **Analytics**: Usage tracking and insights

## Support

For issues or questions:
1. Check browser console for errors
2. Review service worker logs
3. Test in different browsers
4. Contact development team

## License

Copyright © 2024 Tree Service Estimator Pro. All rights reserved.