# Railway Environment Variables - Complete Setup

## Variables to Add in Railway Dashboard

### 1. DATABASE_URL
```
DATABASE_URL=${{POSTGRESQL_URL}}
```
**Note**: Use double curly braces `${{POSTGRESQL_URL}}` in Railway to reference the PostgreSQL plugin's URL

### 2. REDIS_URL  
```
REDIS_URL=${{REDIS_URL}}
```
**Note**: Use double curly braces `${{REDIS_URL}}` in Railway to reference the Redis plugin's URL

### 3. CORS_ORIGINS
```
CORS_ORIGINS=https://cox-tree-quote-app.web.app,https://cox-tree-quote-app.firebaseapp.com
```
**Note**: No quotes or brackets needed in Railway. Multiple origins separated by commas.

### 4. PORT
```
PORT=${{PORT}}
```
**Note**: Railway provides this automatically. Reference it with double curly braces.

### 5. Additional Production Variables
```
ENVIRONMENT=production
ALLOWED_HOSTS=context-engineering-intro-production.up.railway.app
LOG_LEVEL=INFO
LOG_FORMAT=json
DEBUG=False
```

## Complete Environment Variables List

Here's what your Railway dashboard should have:

✅ **Already Set:**
- SECRET_KEY=Gq6_qrsbE...your-existing-key
- GOOGLE_MAPS_API_KEY=your-key
- QUICKBOOKS_CLIENT_ID=your-id
- QUICKBOOKS_CLIENT_SECRET=your-secret
- QUICKBOOKS_COMPANY_ID=your-company-id
- FUEL_API_KEY=your-fuel-key

❌ **Need to Add:**
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

## Important Notes

1. **PostgreSQL Plugin**: Make sure you have PostgreSQL plugin added to your Railway project
2. **Redis Plugin**: Make sure you have Redis plugin added to your Railway project
3. **No Quotes**: Don't use quotes around values in Railway
4. **Variable References**: Use `${{VARIABLE_NAME}}` to reference Railway-provided variables

## After Adding Variables

1. **Trigger Redeploy**: Railway should automatically redeploy after adding variables
2. **Check Logs**: Monitor the deploy logs for any errors
3. **Test Health Endpoint**: 
   ```bash
   curl https://context-engineering-intro-production.up.railway.app/health
   ```

## Troubleshooting

If deployment still fails after adding these variables:

1. **Check PostgreSQL Connection**:
   - Ensure PostgreSQL plugin is attached to your service
   - Check if DATABASE_URL is properly formatted

2. **Check Redis Connection**:
   - Ensure Redis plugin is attached to your service
   - Verify REDIS_URL is accessible

3. **Review Deploy Logs**:
   - Look for specific error messages
   - Check if all dependencies are installing correctly

4. **Verify Dockerfile**:
   - Ensure start.sh has correct permissions
   - Check if PORT variable is being used correctly

## Quick Test Commands

After deployment:
```bash
# Test health endpoint
curl https://context-engineering-intro-production.up.railway.app/health

# Test API root
curl https://context-engineering-intro-production.up.railway.app/

# Test with frontend
# Go to: https://cox-tree-quote-app.web.app
# Should connect automatically to Railway backend
```