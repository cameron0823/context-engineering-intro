# Tree Service Application Deployment Instructions

## Prerequisites
- Firebase CLI installed (`npm install -g firebase-tools`)
- Railway CLI installed (optional, for CLI deployment)
- Git repository initialized

## 1. Firebase Deployment (Frontend)

### First-time setup:
```bash
# Login to Firebase
firebase login

# Initialize Firebase (if not done)
firebase init hosting

# Select or create project "tree-estimate"
# Set public directory to "mobile_app"
# Configure as single-page app: No
# Set up automatic builds: No
```

### Deploy to Firebase:
```bash
# Deploy the mobile app and admin interface
firebase deploy --only hosting

# Your app will be available at:
# - Mobile PWA: https://tree-estimate.web.app
# - Admin Dashboard: https://tree-estimate.web.app/admin
```

## 2. Railway Backend Deployment

### Option A: Deploy via GitHub (Recommended)
1. Push your code to GitHub
2. Go to https://railway.app
3. Create new project → Deploy from GitHub repo
4. Select your repository
5. Railway will auto-detect the Python app

### Option B: Deploy via Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize new project
railway init

# Link to existing project (if needed)
railway link

# Deploy
railway up
```

### Configure Environment Variables in Railway:
1. Go to your Railway project dashboard
2. Click on Variables tab
3. Add the following variables:

```
# These are automatically provided by Railway:
# DATABASE_URL (from PostgreSQL plugin)
# REDIS_URL (from Redis plugin)
# PORT

# You need to add these:
SECRET_KEY=<generate-secure-key>
GOOGLE_MAPS_API_KEY=<your-api-key>
QUICKBOOKS_CLIENT_ID=<your-client-id>
QUICKBOOKS_CLIENT_SECRET=<your-client-secret>
QUICKBOOKS_COMPANY_ID=<your-company-id>
FUEL_API_KEY=<your-api-key>
```

### Add Railway Plugins:
1. PostgreSQL: Click "+ New" → Database → PostgreSQL
2. Redis: Click "+ New" → Database → Redis

## 3. Post-Deployment Configuration

### Update Frontend API URLs:
The mobile app is already configured to use production URLs when not on localhost.

### Initialize Database:
Railway will automatically run migrations on deploy if you have a release command configured.

To manually run migrations:
```bash
railway run alembic upgrade head
```

### Create Admin User:
```bash
railway run python scripts/create_admin_user.py
```

## 4. Verify Deployment

### Test Mobile PWA:
1. Visit https://tree-estimate.web.app
2. Login with test credentials
3. Create a test estimate
4. Verify calculations work

### Test Admin Dashboard:
1. Visit https://tree-estimate.web.app/admin
2. Login with admin credentials
3. Verify all sections load
4. Test pricing configuration

### Test API:
```bash
# Health check
curl https://tree-api.railway.app/health

# API docs (if DEBUG=True)
# Visit https://tree-api.railway.app/docs
```

## 5. Monitoring

### Railway Dashboard:
- View logs: Project → Deployments → View Logs
- Monitor metrics: Project → Metrics
- Set up alerts: Project → Settings → Notifications

### Firebase Console:
- View hosting metrics: Firebase Console → Hosting
- Monitor usage: Firebase Console → Usage and billing

## 6. Updates and Maintenance

### Update Frontend:
```bash
# Make changes to mobile_app/
firebase deploy --only hosting
```

### Update Backend:
```bash
# Push changes to GitHub
git add .
git commit -m "Update message"
git push

# Railway auto-deploys from main branch
```

### Database Migrations:
```bash
# Create new migration locally
alembic revision --autogenerate -m "Description"

# Push to GitHub
git add .
git commit -m "Add migration"
git push

# Railway runs migrations automatically
```

## 7. Rollback Procedures

### Frontend Rollback:
```bash
# List Firebase hosting versions
firebase hosting:releases:list

# Rollback to previous version
firebase hosting:rollback
```

### Backend Rollback:
1. Go to Railway dashboard
2. Navigate to Deployments
3. Click on previous successful deployment
4. Click "Redeploy"

## 8. Security Checklist

- [ ] Strong SECRET_KEY generated
- [ ] DEBUG=False in production
- [ ] All API keys secured
- [ ] HTTPS enforced
- [ ] CORS properly configured
- [ ] Database backups enabled
- [ ] Rate limiting configured
- [ ] Error logging enabled

## 9. Troubleshooting

### Common Issues:

**Frontend not loading:**
- Check Firebase hosting status
- Verify API URLs in api.js
- Check browser console for errors

**API connection errors:**
- Verify Railway deployment status
- Check CORS configuration
- Verify environment variables

**Database errors:**
- Check PostgreSQL connection
- Verify migrations ran
- Check Railway logs

**Authentication issues:**
- Verify SECRET_KEY is set
- Check JWT token expiration
- Verify user roles

### Support Resources:
- Firebase Support: https://firebase.google.com/support
- Railway Docs: https://docs.railway.app
- Project Issues: GitHub Issues page