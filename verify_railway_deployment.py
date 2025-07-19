"""
Railway Deployment Verification Script

This script helps verify Railway deployment configuration and troubleshoot issues.
"""
import os
import sys
import json
import requests
from typing import Dict, Any

# Railway deployment URL
RAILWAY_URL = "https://context-engineering-intro-production.up.railway.app"
FIREBASE_URL = "https://cox-tree-quote-app.web.app"

def check_environment_variables():
    """Check if all required environment variables would be set correctly."""
    print("🔍 Checking Environment Variable Configuration...")
    print("\n" + "="*60)
    
    required_vars = {
        "DATABASE_URL": "${{POSTGRESQL_URL}}",
        "REDIS_URL": "${{REDIS_URL}}",
        "CORS_ORIGINS": "https://cox-tree-quote-app.web.app,https://cox-tree-quote-app.firebaseapp.com",
        "PORT": "${{PORT}}",
        "ENVIRONMENT": "production",
        "ALLOWED_HOSTS": "context-engineering-intro-production.up.railway.app",
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "json",
        "DEBUG": "False"
    }
    
    print("📋 Required Environment Variables for Railway:\n")
    for var, value in required_vars.items():
        print(f"{var}={value}")
    
    print("\n✅ Copy and paste these into Railway's environment variables section")
    print("="*60)

def test_railway_endpoints():
    """Test Railway deployment endpoints."""
    print("\n🧪 Testing Railway Endpoints...")
    print("="*60)
    
    endpoints = [
        ("Health Check", f"{RAILWAY_URL}/health", "GET"),
        ("API Root", f"{RAILWAY_URL}/", "GET"),
        ("API Docs", f"{RAILWAY_URL}/docs", "GET")
    ]
    
    for name, url, method in endpoints:
        print(f"\n📍 Testing {name}: {url}")
        try:
            response = requests.request(method, url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success!")
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection Error - Service may be down")
        except requests.exceptions.Timeout:
            print("   ❌ Timeout - Service is not responding")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_cors_configuration():
    """Test CORS configuration between Firebase and Railway."""
    print("\n🌐 Testing CORS Configuration...")
    print("="*60)
    
    # Test preflight request
    print(f"\n📍 Testing CORS preflight from {FIREBASE_URL}")
    
    headers = {
        'Origin': FIREBASE_URL,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type,authorization'
    }
    
    try:
        response = requests.options(f"{RAILWAY_URL}/api/auth/login", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        for header, value in cors_headers.items():
            if value:
                print(f"   ✅ {header}: {value}")
            else:
                print(f"   ❌ {header}: Not set")
                
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def generate_diagnostic_report():
    """Generate a diagnostic report for Railway deployment issues."""
    print("\n📊 Diagnostic Report")
    print("="*60)
    
    print("\n🔍 Common Railway 502 Error Causes:\n")
    
    issues = [
        {
            "issue": "Missing PORT environment variable",
            "solution": "Add PORT=${{PORT}} to Railway environment variables",
            "check": "Look for 'Starting server on port' in deploy logs"
        },
        {
            "issue": "Database connection failure",
            "solution": "Ensure DATABASE_URL=${{POSTGRESQL_URL}} is set",
            "check": "Look for 'connection refused' or 'could not connect to server' in logs"
        },
        {
            "issue": "Redis connection failure",
            "solution": "Ensure REDIS_URL=${{REDIS_URL}} is set",
            "check": "Look for Redis connection errors in logs"
        },
        {
            "issue": "Pydantic v2 compatibility",
            "solution": "Already fixed! The migration script has been run",
            "check": "✅ Completed"
        },
        {
            "issue": "Missing dependencies",
            "solution": "Check if all packages in requirements.txt installed",
            "check": "Look for ImportError in deploy logs"
        }
    ]
    
    for i, item in enumerate(issues, 1):
        print(f"{i}. 🔸 {item['issue']}")
        print(f"   💡 Solution: {item['solution']}")
        print(f"   🔍 How to check: {item['check']}\n")

def create_test_admin_user():
    """Create a test script for admin user creation."""
    print("\n👤 Admin User Test")
    print("="*60)
    
    print("Once Railway is running, you can create an admin user with:")
    print("\n```bash")
    print("# SSH into Railway service or run locally")
    print("python create_local_admin.py")
    print("```")
    
    print("\nOr use the existing admin credentials from CAMERON_ADMIN_CREDENTIALS.json")

def main():
    """Run all verification steps."""
    print("🚀 Railway Deployment Verification Tool")
    print("="*60)
    
    # Step 1: Show required environment variables
    check_environment_variables()
    
    # Step 2: Test Railway endpoints
    test_railway_endpoints()
    
    # Step 3: Test CORS configuration
    test_cors_configuration()
    
    # Step 4: Generate diagnostic report
    generate_diagnostic_report()
    
    # Step 5: Admin user info
    create_test_admin_user()
    
    print("\n✅ Verification Complete!")
    print("="*60)
    print("\n📌 Next Steps:")
    print("1. Add any missing environment variables to Railway")
    print("2. Trigger a new deployment")
    print("3. Check the deploy logs for any errors")
    print("4. Run this script again to verify the deployment is working")

if __name__ == "__main__":
    main()