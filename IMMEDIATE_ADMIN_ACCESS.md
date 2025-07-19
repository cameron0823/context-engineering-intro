# Getting Admin Access RIGHT NOW

Since Railway is still having issues, here are TWO ways to get admin access immediately:

## Option 1: Run Backend Locally (Recommended)

### Step 1: Start Your Local Backend
Open a NEW terminal/command prompt and run:
```bash
cd C:\Users\Cameron Cox\Documents\Development\context-engineering-intro
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Your backend will start at: http://localhost:8000

### Step 2: Create Admin Account
In your CURRENT terminal, run:
```bash
python create_local_admin.py
```

This will create:
- Username: `admin`
- Password: `AdminPass123!`

### Step 3: Access Admin Dashboard
Since your Firebase frontend is configured for Railway, you have two options:

**Option A: Use Browser Developer Console** (Quick Hack)
1. Go to https://cox-tree-quote-app.web.app/admin
2. Open browser console (F12)
3. Type: `window.api.baseUrl = 'http://localhost:8000/api'`
4. Press Enter
5. Now login with admin credentials

**Option B: Run Frontend Locally**
1. Open the `mobile_app/index.html` file directly in your browser
2. Navigate to `/admin` 
3. Login with admin credentials

## Option 2: Wait for Railway Fix

Monitor your Railway dashboard at https://railway.app/dashboard
The deployment should complete within 5-10 minutes after our fix.

## What You Can Do as Admin

Once logged in, you can:
- ✅ Create more user accounts
- ✅ Update pricing and rates
- ✅ View all estimates
- ✅ Access reports
- ✅ Configure system settings

## Default Admin Credentials

```
Username: admin
Password: AdminPass123!
```

**IMPORTANT**: Change this password after first login!

## Still Having Issues?

1. **Backend won't start locally?**
   - Make sure you're in the right directory
   - Activate virtual environment first
   - Install requirements.txt

2. **Can't create admin account?**
   - Ensure backend is running (check http://localhost:8000/health)
   - Check for error messages in terminal

3. **Can't login to admin dashboard?**
   - Clear browser cache
   - Try incognito/private mode
   - Check browser console for errors

## Quick Test Commands

Test if backend is running:
```bash
curl http://localhost:8000/health
```

Test if Railway is working (when it's fixed):
```bash
curl https://context-engineering-intro-production.up.railway.app/health
```