#!/usr/bin/env python3
"""
Simple authentication test to verify the fix is working
"""
import requests
import json

BASE_URL = "http://localhost:8002"

print("Testing Tree Service App Authentication...")
print("=" * 50)

# Test 1: Check if app is running
try:
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print("✅ App is running")
        data = response.json()
        print(f"   Version: {data.get('version', 'Unknown')}")
    else:
        print(f"❌ App returned status: {response.status_code}")
except Exception as e:
    print(f"❌ Cannot connect to app: {str(e)}")
    print("\nPlease start the app first:")
    print("  python start_dev_server.py")
    exit(1)

# Test 2: Try to login with test credentials
print("\nTesting authentication...")

test_users = [
    {"username": "admin", "password": "Admin123!", "role": "admin"},
    {"username": "estimator", "password": "Estimator123!", "role": "estimator"}
]

for user in test_users:
    print(f"\nTesting {user['role']} login...")
    
    # Try login
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": user["username"],
            "password": user["password"]
        }
    )
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token", "")
        
        print(f"✅ Login successful for {user['username']}")
        print(f"   Token: {token[:20]}...")
        
        # Test authenticated endpoint
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token works! User role: {user_data.get('role', 'Unknown')}")
        else:
            print(f"❌ Token validation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    else:
        print(f"❌ Login failed for {user['username']}: {response.status_code}")
        print(f"   Response: {response.text}")

# Test 3: Test calculator endpoint
print("\n" + "=" * 50)
print("Quick functionality test...")

# Login as admin first
response = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={"username": "admin", "password": "Admin123!"}
)

if response.status_code == 200:
    token = response.json()["access_token"]
    
    # Simple calculation
    calc_data = {
        "travel_details": {
            "miles": 10.0,
            "estimated_minutes": 20,
            "vehicle_rate_per_mile": 0.65,
            "driver_hourly_rate": 25.00
        },
        "labor_details": {
            "estimated_hours": 2.0,
            "crew": [{"name": "Worker", "hourly_rate": 35.00}],
            "emergency": False,
            "weekend": False
        },
        "disposal_fees": 50.00,
        "permit_cost": 0.00,
        "margins": {
            "overhead_percent": 25.0,
            "profit_percent": 35.0,
            "safety_buffer_percent": 10.0
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/estimates/calculate",
        json=calc_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Calculator works! Final total: ${result.get('final_total', 0)}")
    else:
        print(f"❌ Calculator failed: {response.status_code}")

print("\n" + "=" * 50)
print("Summary: Authentication fix appears to be", end=" ")
print("WORKING ✅" if response.status_code == 200 else "NOT WORKING ❌")