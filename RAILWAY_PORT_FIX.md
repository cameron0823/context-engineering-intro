# Fix Railway PORT Error

## The Problem
Railway is showing: "PORT variable must be integer between 0 and 65535"

## The Solution
**Remove the PORT environment variable from your Railway settings!**

Railway automatically provides the PORT variable. When you manually set `PORT=${{PORT}}`, it creates a circular reference that doesn't resolve to a number.

## Steps to Fix:

1. Go to your Railway dashboard
2. Click on your service
3. Go to "Variables" tab
4. **DELETE** the PORT variable (click the X next to it)
5. Railway will automatically provide the correct PORT

## Why This Works:
- Railway automatically injects a PORT environment variable (like 5234)
- You don't need to set it manually
- The app will receive the correct port number automatically

## After Removing PORT:
Your service should restart and the error should be gone!

## Verify It's Working:
Check the deployment logs for:
```
Starting server on port 5234...
```
(The actual port number will vary)