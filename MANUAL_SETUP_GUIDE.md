# Manual Setup Guide - If Railway Has Issues

## Current Status
- ✅ Frontend deployed to Firebase: https://cox-tree-quote-app.web.app
- ✅ Admin interface available: https://cox-tree-quote-app.web.app/admin
- ❌ Backend on Railway showing 502 error
- ⏳ User accounts need to be created

## Quick Start with Local Backend

If Railway continues to have issues, you can run the backend locally for testing:

### 1. Start Backend Locally
```bash
cd context-engineering-intro
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn src.main:app --reload --port 8000
```

### 2. Update Frontend to Use Local Backend
The frontend is already configured to use localhost when developing locally.

### 3. Create Users Manually
With the backend running locally, you can:

#### Option A: Use the setup script
1. Edit `setup_live_app.py` and change line 10:
   ```python
   API_URL = "http://localhost:8000/api"
   ```
2. Run: `python setup_live_app.py`

#### Option B: Manual API calls
Use a tool like Postman or curl to create users:

```bash
# Register admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@coxtreeservice.com",
    "password": "AdminPass123!",
    "full_name": "System Administrator",
    "role": "admin"
  }'

# Register other users...
```

## Team Access Without Railway

### For Testing Locally

**Field Estimators:**
1. Open http://localhost:3000 (or wherever frontend runs locally)
2. Login with created credentials
3. Test creating estimates

**Office/Management:**
1. Open http://localhost:3000/admin
2. Login with manager/admin credentials
3. Test approving estimates

## Temporary Workaround Instructions

Until Railway is fixed, your team can:

1. **Use the Firebase frontend** - It's fully deployed and functional
2. **Run backend locally** - One person can run the backend on their machine
3. **Use ngrok** - Expose local backend to internet temporarily:
   ```bash
   # Install ngrok
   # Run: ngrok http 8000
   # Update frontend API URL with ngrok URL
   ```

## What's Working Now

Even without the backend, you can:
- ✅ Access the mobile app interface
- ✅ Access the admin dashboard
- ✅ See the UI and understand the workflow
- ✅ Work offline (estimates save locally)

## Railway Fix Checklist

When trying to fix Railway:

- [ ] Check Railway logs for specific error
- [ ] Verify all environment variables are set
- [ ] Ensure PostgreSQL and Redis are running
- [ ] Check if PORT environment variable is used
- [ ] Verify Dockerfile is building correctly
- [ ] Try redeploying from GitHub
- [ ] Check Railway status page for issues

## Emergency Contact Setup

If you need to get the app running immediately:

1. **Local Development**
   - One team member runs backend locally
   - Others connect to their machine's IP

2. **Alternative Hosting**
   - Deploy to Heroku (similar to Railway)
   - Use DigitalOcean App Platform
   - Deploy to AWS Elastic Beanstalk

3. **Quick Demo**
   - Use the UI without backend
   - Show workflow and features
   - Explain full functionality

## Success Criteria

The app is fully functional when:
- [ ] Backend responds at Railway URL
- [ ] Users can login on mobile app
- [ ] Estimates can be created and synced
- [ ] Admin dashboard shows real data
- [ ] Email notifications work (if configured)