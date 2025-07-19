@echo off
REM Tree Service Application Deployment Script for Windows

echo Tree Service Application Deployment
echo ======================================

REM Check if Firebase CLI is installed
where firebase >nul 2>nul
if %errorlevel% neq 0 (
    echo Firebase CLI not found. Please install it first:
    echo    npm install -g firebase-tools
    exit /b 1
)

REM Deploy Frontend to Firebase
echo.
echo Deploying Frontend to Firebase...
echo -----------------------------------
firebase deploy --only hosting

if %errorlevel% equ 0 (
    echo Frontend deployed successfully!
    echo    - Mobile PWA: https://tree-estimate.web.app
    echo    - Admin Dashboard: https://tree-estimate.web.app/admin
) else (
    echo Frontend deployment failed!
    exit /b 1
)

REM Backend deployment instructions
echo.
echo Backend Deployment (Railway)
echo ------------------------------
echo To deploy the backend to Railway:
echo.
echo 1. Push your code to GitHub:
echo    git add .
echo    git commit -m "Deploy to Railway"
echo    git push origin main
echo.
echo 2. Railway will automatically deploy from GitHub
echo    - API URL: https://tree-api.railway.app
echo.
echo 3. Make sure to set environment variables in Railway dashboard
echo.

REM Final message
echo Deployment Complete!
echo =======================
echo.
echo Next steps:
echo 1. Test the mobile app at https://tree-estimate.web.app
echo 2. Test the admin dashboard at https://tree-estimate.web.app/admin
echo 3. Verify API health at https://tree-api.railway.app/health
echo.
echo For detailed instructions, see DEPLOYMENT_INSTRUCTIONS.md
pause