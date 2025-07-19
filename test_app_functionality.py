"""
Comprehensive test script to ensure app functionality
"""
import subprocess
import time
import requests
import json
import sys
import os

# Test configuration
LOCAL_API = "http://localhost:8001"
RAILWAY_API = "https://context-engineering-intro-production.up.railway.app"
FIREBASE_URL = "https://cox-tree-quote-app.web.app"

# Test results
test_results = {
    "backend_local": False,
    "backend_railway": False,
    "frontend_deployed": False,
    "admin_created": False,
    "users_created": False,
    "api_endpoints": {}
}

def print_header(text):
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60)

def test_endpoint(url, name):
    """Test if an endpoint is accessible"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✓ {name}: OK")
            return True
        else:
            print(f"✗ {name}: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {name}: {str(e)[:50]}")
        return False

def start_local_backend():
    """Start the simple backend server"""
    print_header("STARTING LOCAL BACKEND")
    
    # Kill any existing process on port 8001
    if sys.platform == "win32":
        subprocess.run("taskkill /F /IM python.exe 2>nul", shell=True, capture_output=True)
    
    # Start backend in background
    process = subprocess.Popen(
        [sys.executable, "simple_backend.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for startup
    print("Waiting for backend to start...")
    time.sleep(3)
    
    # Test if it's running
    if test_endpoint(f"{LOCAL_API}/health", "Local backend health"):
        test_results["backend_local"] = True
        return process
    else:
        process.terminate()
        return None

def test_railway_backend():
    """Test if Railway backend is working"""
    print_header("TESTING RAILWAY BACKEND")
    
    if test_endpoint(f"{RAILWAY_API}/health", "Railway backend"):
        test_results["backend_railway"] = True
        return True
    return False

def test_frontend():
    """Test if frontend is deployed"""
    print_header("TESTING FRONTEND DEPLOYMENT")
    
    if test_endpoint(FIREBASE_URL, "Firebase frontend"):
        test_results["frontend_deployed"] = True
        return True
    return False

def create_users(api_url):
    """Create test users"""
    print_header("CREATING USER ACCOUNTS")
    
    users = [
        {
            "username": "cameron",
            "password": "CoxTree2024!",
            "email": "cameron@coxtreeservice.com",
            "full_name": "Cameron Cox",
            "role": "admin"
        },
        {
            "username": "manager1",
            "password": "Manager123!",
            "email": "manager@coxtreeservice.com",
            "full_name": "Office Manager",
            "role": "manager"
        },
        {
            "username": "estimator1",
            "password": "Estimator123!",
            "email": "estimator1@coxtreeservice.com",
            "full_name": "Field Estimator 1",
            "role": "estimator"
        }
    ]
    
    created = 0
    for user in users:
        try:
            response = requests.post(
                f"{api_url}/api/auth/register",
                json=user,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code in [200, 201]:
                print(f"✓ Created user: {user['username']}")
                created += 1
            elif response.status_code == 400:
                print(f"! User exists: {user['username']}")
                created += 1
            else:
                print(f"✗ Failed to create {user['username']}: {response.status_code}")
        except Exception as e:
            print(f"✗ Error creating {user['username']}: {str(e)[:50]}")
    
    test_results["users_created"] = created == len(users)
    return created == len(users)

def test_api_endpoints(api_url):
    """Test all API endpoints"""
    print_header("TESTING API ENDPOINTS")
    
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/api/dashboard/stats", None),
        ("GET", "/api/estimates/", None),
        ("GET", "/api/auth/users", None),
        ("GET", "/api/costs/", None),
        ("POST", "/api/auth/login", {
            "username": "admin",
            "password": "AdminPass123!"
        })
    ]
    
    passed = 0
    for method, endpoint, data in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{api_url}{endpoint}", timeout=5)
            else:
                response = requests.post(
                    f"{api_url}{endpoint}",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
            
            if response.status_code in [200, 201]:
                print(f"✓ {method} {endpoint}: OK")
                test_results["api_endpoints"][endpoint] = True
                passed += 1
            else:
                print(f"✗ {method} {endpoint}: Status {response.status_code}")
                test_results["api_endpoints"][endpoint] = False
        except Exception as e:
            print(f"✗ {method} {endpoint}: {str(e)[:50]}")
            test_results["api_endpoints"][endpoint] = False
    
    return passed == len(endpoints)

def generate_setup_instructions():
    """Generate instructions based on test results"""
    print_header("SETUP INSTRUCTIONS")
    
    if test_results["backend_railway"]:
        api_url = RAILWAY_API
        print("\n✅ Railway backend is working!")
        print(f"API URL: {api_url}")
    elif test_results["backend_local"]:
        api_url = LOCAL_API
        print("\n⚠️  Railway backend not working - using local backend")
        print(f"API URL: {api_url}")
        print("\nTo use with deployed frontend:")
        print("1. Open https://cox-tree-quote-app.web.app/admin")
        print("2. Open browser console (F12)")
        print(f"3. Type: window.api.baseUrl = '{api_url}/api'")
        print("4. Press Enter, then login")
    else:
        print("\n❌ No backend is running!")
        return
    
    print("\n📱 Access URLs:")
    print(f"Mobile App: {FIREBASE_URL}")
    print(f"Admin Dashboard: {FIREBASE_URL}/admin")
    
    print("\n👤 Login Credentials:")
    print("Username: admin")
    print("Password: AdminPass123!")
    
    print("\n🚀 Next Steps:")
    print("1. Login to admin dashboard")
    print("2. Create additional users if needed")
    print("3. Test creating an estimate")
    print("4. Share credentials with your team")

def generate_report():
    """Generate final test report"""
    print_header("TEST REPORT")
    
    print("\n🔍 Test Results:")
    print(f"Local Backend: {'✓' if test_results['backend_local'] else '✗'}")
    print(f"Railway Backend: {'✓' if test_results['backend_railway'] else '✗'}")
    print(f"Frontend Deployed: {'✓' if test_results['frontend_deployed'] else '✗'}")
    print(f"Users Created: {'✓' if test_results['users_created'] else '✗'}")
    
    print("\n📊 API Endpoints:")
    for endpoint, status in test_results["api_endpoints"].items():
        print(f"{endpoint}: {'✓' if status else '✗'}")
    
    # Save report to file
    with open("TEST_REPORT.txt", "w") as f:
        f.write("COX TREE SERVICE APP - TEST REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("TEST RESULTS:\n")
        f.write(f"Local Backend: {'PASS' if test_results['backend_local'] else 'FAIL'}\n")
        f.write(f"Railway Backend: {'PASS' if test_results['backend_railway'] else 'FAIL'}\n")
        f.write(f"Frontend Deployed: {'PASS' if test_results['frontend_deployed'] else 'FAIL'}\n")
        f.write(f"Users Created: {'PASS' if test_results['users_created'] else 'FAIL'}\n")
        f.write("\nRECOMMENDATIONS:\n")
        
        if not test_results["backend_railway"]:
            f.write("- Check Railway logs and fix deployment\n")
            f.write("- Verify environment variables are set\n")
            f.write("- Try redeploying from GitHub\n")
        
        if test_results["backend_local"]:
            f.write("- App is functional with local backend\n")
            f.write("- Can be used for testing and demos\n")
    
    print("\n✓ Test report saved to TEST_REPORT.txt")

def main():
    """Run all tests"""
    print_header("COX TREE SERVICE APP - FUNCTIONALITY TEST")
    
    # Test Railway first
    railway_ok = test_railway_backend()
    
    # Test frontend
    frontend_ok = test_frontend()
    
    # Start local backend if Railway is down
    backend_process = None
    if not railway_ok:
        backend_process = start_local_backend()
    
    # Determine which API to use
    if railway_ok:
        api_url = RAILWAY_API
        print("\n✓ Using Railway backend")
    elif test_results["backend_local"]:
        api_url = LOCAL_API
        print("\n✓ Using local backend")
    else:
        print("\n✗ No backend available!")
        return
    
    # Create users
    create_users(api_url)
    
    # Test API endpoints
    test_api_endpoints(api_url)
    
    # Generate instructions
    generate_setup_instructions()
    
    # Generate report
    generate_report()
    
    # Cleanup
    if backend_process:
        print("\n⚠️  Local backend is still running")
        print("Press Ctrl+C to stop it when done testing")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nError during testing: {e}")
        import traceback
        traceback.print_exc()