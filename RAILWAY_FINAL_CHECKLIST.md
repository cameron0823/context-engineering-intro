# Railway Deployment - Final Checklist

## ✅ Step-by-Step Configuration

### 1. Add Database and Redis Plugins (if not already done)
- [ ] Go to your Railway project
- [ ] Click "New" → "Database" → "Add PostgreSQL"
- [ ] Click "New" → "Database" → "Add Redis"
- [ ] Wait for both to provision

### 2. Add Missing Environment Variables
Copy and paste these exactly into Railway's environment variables:

```
DATABASE_URL=${{POSTGRESQL_URL}}
REDIS_URL=${{REDIS_URL}}
CORS_ORIGINS=https://cox-tree-quote-app.web.app,https://cox-tree-quote-app.firebaseapp.com
PORT=${{PORT}}
ENVIRONMENT=production
ALLOWED_HOSTS=context-engineering-intro-production.up.railway.app
LOG_LEVEL=INFO
LOG_FORMAT=json
DEBUG=False
```

### 3. Verify All Variables Are Set
Your Railway service should have these variables:
- [x] SECRET_KEY
- [x] GOOGLE_MAPS_API_KEY  
- [x] QUICKBOOKS_CLIENT_ID
- [x] QUICKBOOKS_CLIENT_SECRET
- [x] QUICKBOOKS_COMPANY_ID
- [x] FUEL_API_KEY
- [ ] DATABASE_URL
- [ ] REDIS_URL
- [ ] CORS_ORIGINS
- [ ] PORT
- [ ] ENVIRONMENT
- [ ] ALLOWED_HOSTS
- [ ] LOG_LEVEL
- [ ] LOG_FORMAT
- [ ] DEBUG

### 4. Trigger Deployment
- [ ] Click "Deploy" or push to GitHub to trigger auto-deploy
- [ ] Watch the build logs for errors
- [ ] Wait for deployment to complete

### 5. Test Deployment
```bash
# Test 1: Health check
curl https://context-engineering-intro-production.up.railway.app/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "cache": {"status": "healthy"},
    "external_apis": {...}
  }
}

# Test 2: API root
curl https://context-engineering-intro-production.up.railway.app/

# Expected response:
{
  "app": "Tree Service Estimating",
  "version": "1.0.0",
  "environment": "production"
}
```

### 6. Test Frontend Integration
1. Open https://cox-tree-quote-app.web.app/admin
2. Open browser console (F12)
3. Check for any CORS errors
4. Try to login with your credentials

### 7. If Still Getting 502 Error

Check these common issues:

1. **Database Connection**:
   - Is PostgreSQL plugin attached?
   - Check logs for database connection errors

2. **Missing Dependencies**:
   - Check if all Python packages installed correctly
   - Look for import errors in logs

3. **PORT Configuration**:
   - Ensure PORT=${{PORT}} is set
   - Check if start.sh is executable

4. **Memory/Resource Limits**:
   - Railway free tier has limits
   - Check if app is running out of memory

### 8. View Logs
```bash
# In Railway dashboard:
1. Click on your service
2. Go to "Deployments" tab
3. Click on latest deployment
4. View "Deploy Logs" and "Runtime Logs"

# Look for:
- "Starting server on port XXXX"
- "Application startup complete"
- Any error messages
```

## Quick Fix Commands

If you need to test locally while Railway is being fixed:

```bash
# Start local backend
python simple_backend.py

# In browser console at https://cox-tree-quote-app.web.app
window.api.baseUrl = 'http://localhost:8001/api'
```

## Success Indicators

You'll know it's working when:
1. ✅ Health endpoint returns 200 OK
2. ✅ No CORS errors in browser console
3. ✅ Can login from Firebase frontend
4. ✅ Database operations persist data
5. ✅ No 502 errors

Good luck! 🚀