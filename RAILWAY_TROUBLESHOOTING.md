# Railway Deployment Troubleshooting Guide

## Current Issue: 502 Bad Gateway Error

The Railway deployment at `https://context-engineering-intro-production.up.railway.app` is returning a 502 error, which means the application is not responding properly.

## Immediate Steps to Check

### 1. Check Railway Dashboard Logs
1. Go to your Railway dashboard
2. Click on your service
3. Check the "Logs" tab for any error messages
4. Common issues to look for:
   - Port binding errors
   - Database connection failures
   - Missing environment variables
   - Python module import errors

### 2. Verify Environment Variables
Ensure these are set in Railway dashboard:
```
DATABASE_URL=postgresql://[from Railway PostgreSQL]
REDIS_URL=redis://[from Railway Redis]
SECRET_KEY=[generate a secure random key]
ALLOWED_HOSTS=context-engineering-intro-production.up.railway.app
CORS_ORIGINS=https://cox-tree-quote-app.web.app
PORT=8000
```

### 3. Check Service Health
The app should be accessible at these endpoints once running:
- Health check: `https://context-engineering-intro-production.up.railway.app/health`
- Root: `https://context-engineering-intro-production.up.railway.app/`
- API endpoints: `https://context-engineering-intro-production.up.railway.app/api/[endpoint]`

## Common Railway Fixes

### Fix 1: Restart the Service
1. In Railway dashboard, click "Settings"
2. Click "Restart" to restart the service
3. Wait 2-3 minutes for deployment
4. Check logs for startup messages

### Fix 2: Redeploy from GitHub
1. Make a small change to any file (like adding a comment)
2. Commit and push to GitHub
3. Railway will automatically redeploy
4. Monitor the build logs

### Fix 3: Check Build Configuration
Ensure your Railway service has:
- Build command: (leave empty, uses Dockerfile)
- Start command: (leave empty, uses Dockerfile CMD)
- Port: Should be automatically detected

### Fix 4: Database Initialization
If the app starts but has database errors:
1. In Railway, go to your PostgreSQL service
2. Click "Connect" and copy the connection string
3. Use a PostgreSQL client to connect
4. Run any missing migrations manually

## Testing Once Fixed

### 1. Test API Connection
```bash
# Test health endpoint
curl https://context-engineering-intro-production.up.railway.app/health

# Should return:
# {"status":"healthy","version":"0.1.0","environment":"production"}
```

### 2. Run Setup Script
Once the API is responding:
```bash
python setup_live_app.py
```

This will:
- Create initial user accounts
- Configure pricing
- Generate team access information

### 3. Test Frontend Access
- Mobile App: https://cox-tree-quote-app.web.app
- Admin Dashboard: https://cox-tree-quote-app.web.app/admin

## If Railway Continues to Fail

### Alternative: Run Locally for Testing
1. Start the backend locally:
   ```bash
   cd context-engineering-intro
   uvicorn src.main:app --reload
   ```

2. Update `setup_live_app.py` to use local URL:
   ```python
   API_URL = "http://localhost:8000/api"
   ```

3. Run setup script locally to create users

### Alternative: Check Railway Status
- Visit https://status.railway.app/ to check for platform issues
- Join Railway Discord for community support
- Check Railway documentation for FastAPI deployment guides

## Environment Variable Template

Here's what you need in Railway (copy and modify):
```
# Database (from Railway PostgreSQL)
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/railway

# Redis (from Railway Redis) 
REDIS_URL=redis://default:[password]@[host]:[port]

# Security
SECRET_KEY=your-very-long-random-secret-key-here

# Allowed hosts
ALLOWED_HOSTS=context-engineering-intro-production.up.railway.app

# CORS
CORS_ORIGINS=https://cox-tree-quote-app.web.app

# Port (Railway provides this)
PORT=$PORT

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Next Steps After Fixing

1. Run `setup_live_app.py` to create users
2. Test login on both mobile and admin interfaces
3. Create a test estimate to verify full functionality
4. Share TEAM_ACCESS_INFO.txt with your team