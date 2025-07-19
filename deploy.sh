#!/bin/bash

# Tree Service Application Deployment Script

echo "🚀 Tree Service Application Deployment"
echo "======================================"

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found. Please install it first:"
    echo "   npm install -g firebase-tools"
    exit 1
fi

# Deploy Frontend to Firebase
echo ""
echo "📱 Deploying Frontend to Firebase..."
echo "-----------------------------------"
firebase deploy --only hosting

if [ $? -eq 0 ]; then
    echo "✅ Frontend deployed successfully!"
    echo "   - Mobile PWA: https://tree-estimate.web.app"
    echo "   - Admin Dashboard: https://tree-estimate.web.app/admin"
else
    echo "❌ Frontend deployment failed!"
    exit 1
fi

# Backend deployment instructions
echo ""
echo "🔧 Backend Deployment (Railway)"
echo "------------------------------"
echo "To deploy the backend to Railway:"
echo ""
echo "1. Push your code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Deploy to Railway'"
echo "   git push origin main"
echo ""
echo "2. Railway will automatically deploy from GitHub"
echo "   - API URL: https://tree-api.railway.app"
echo ""
echo "3. Make sure to set environment variables in Railway dashboard"
echo ""

# Final message
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "Next steps:"
echo "1. Test the mobile app at https://tree-estimate.web.app"
echo "2. Test the admin dashboard at https://tree-estimate.web.app/admin"
echo "3. Verify API health at https://tree-api.railway.app/health"
echo ""
echo "For detailed instructions, see DEPLOYMENT_INSTRUCTIONS.md"