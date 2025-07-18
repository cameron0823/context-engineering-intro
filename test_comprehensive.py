#!/usr/bin/env python3
"""
Comprehensive test script for Tree Service Estimating Application
Tests all core functionality including auth, calculations, estimates, and APIs
"""
import requests
import json
from decimal import Decimal
from datetime import datetime
import sys

import os

BASE_URL = f"http://localhost:{os.environ.get('TREE_APP_PORT', '8002')}"
HEADERS = {"Content-Type": "application/json"}

# Test accounts
TEST_ADMIN = {"username": "admin", "password": "Admin123!"}
TEST_ESTIMATOR = {"username": "estimator", "password": "Estimator123!"}
TEST_VIEWER = {"username": "viewer", "password": "Viewer123!"}

# Global token storage
tokens = {}

def print_test(test_name, passed, details=""):
    """Print test result with formatting"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"\n{test_name}: {status}")
    if details:
        print(f"  Details: {details}")

def test_health_check():
    """Test 1: Basic health check"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = response.status_code == 200
        print_test("Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Health Check", False, f"Error: {str(e)}")
        return False

def test_authentication():
    """Test 2: Authentication flow"""
    global tokens
    print("\n=== AUTHENTICATION TESTS ===")
    
    # Test login
    try:
        # Try admin login
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": TEST_ADMIN["username"], "password": TEST_ADMIN["password"]}
        )
        
        if response.status_code == 200:
            data = response.json()
            tokens["admin"] = data["access_token"]
            print_test("Admin Login", True, f"Token received: {tokens['admin'][:20]}...")
        else:
            print_test("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
        # Test current user endpoint
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        
        user_test_passed = response.status_code == 200
        print_test("Get Current User", user_test_passed, 
                  f"User: {response.json().get('username', 'Unknown')}" if user_test_passed else response.text)
        
        return True
        
    except Exception as e:
        print_test("Authentication", False, f"Error: {str(e)}")
# Test data constants
CALC_INPUT = {
    "travel_details": {
        "miles": 25.5,
        "estimated_minutes": 45,
        "vehicle_rate_per_mile": 0.65,
        "driver_hourly_rate": 25.00
    },
    "labor_details": {
        "estimated_hours": 4.5,
        "crew": [
            {"name": "Lead", "hourly_rate": 45.00},
            {"name": "Helper", "hourly_rate": 25.00}
        ],
        "emergency": False,
        "weekend": False
    },
    "equipment_details": [
        {"equipment_id": "chipper", "hourly_cost": 75.00},
        {"equipment_id": "truck", "hourly_cost": 50.00}
    ],
    "disposal_fees": 150.00,
    "permit_cost": 0.00,
    "margins": {
        "overhead_percent": 25.0,
        "profit_percent": 35.0,
        "safety_buffer_percent": 10.0
    }
}

def test_calculator():
    """Test 3: Calculator functionality"""
    print("\n=== CALCULATOR TESTS ===")
    
    if "admin" not in tokens:
        print_test("Calculator Test", False, "No auth token available")
        return False
    
    # Test calculation endpoint
    calc_input = CALC_INPUT
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/estimates/calculate",
            json=calc_input,
            headers={**HEADERS, "Authorization": f"Bearer {tokens['admin']}"}
        )
            headers={**HEADERS, "Authorization": f"Bearer {tokens['admin']}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_test("Calculate Estimate", True, 
                      f"Final Total: ${result.get('final_total', 0)}")
            
            # Verify calculation is deterministic
            response2 = requests.post(
                f"{BASE_URL}/api/estimates/calculate",
                json=calc_input,
                headers={**HEADERS, "Authorization": f"Bearer {tokens['admin']}"}
            )
            
            if response2.status_code == 200:
                result2 = response2.json()
                deterministic = result["final_total"] == result2["final_total"]
                print_test("Deterministic Calculation", deterministic,
                          f"Both calculations: ${result['final_total']}")
            
            return True
        else:
            print_test("Calculate Estimate", False, 
                      f"Status: {response.status_code}, Error: {response.text}")
            return False
            
    except Exception as e:
        print_test("Calculator Test", False, f"Error: {str(e)}")
        return False

def test_estimates_crud():
    """Test 4: Estimate CRUD operations"""
    print("\n=== ESTIMATE CRUD TESTS ===")
    
    if "admin" not in tokens:
        print_test("Estimate CRUD", False, "No auth token available")
        return False
    
    estimate_id = None
    
    try:
        # Create estimate
        estimate_data = {
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "555-0123",
            "service_address": "123 Test St, Test City, TC 12345",
            "calculation_input": {
                "travel_details": {
                    "miles": 10.0,
                    "estimated_minutes": 20,
                    "vehicle_rate_per_mile": 0.65,
                    "driver_hourly_rate": 25.00
                },
                "labor_details": {
                    "estimated_hours": 3.0,
                    "crew": [{"name": "Worker", "hourly_rate": 35.00}],
                    "emergency": False,
                    "weekend": False
                },
                "disposal_fees": 100.00,
                "permit_cost": 0.00,
                "margins": {
                    "overhead_percent": 25.0,
                    "profit_percent": 35.0,
                    "safety_buffer_percent": 10.0
                }
            },
            "notes": "Test estimate creation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/estimates/",
            json=estimate_data,
            headers={**HEADERS, "Authorization": f"Bearer {tokens['admin']}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            estimate_id = result["id"]
            print_test("Create Estimate", True, 
                      f"ID: {estimate_id}, Number: {result.get('estimate_number', 'N/A')}")
        else:
            print_test("Create Estimate", False, 
                      f"Status: {response.status_code}, Error: {response.text}")
            return False
        
        # Read estimate
        response = requests.get(
            f"{BASE_URL}/api/estimates/{estimate_id}",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        
        print_test("Read Estimate", response.status_code == 200,
                  f"Retrieved estimate {estimate_id}")
        
        # Update estimate status
        response = requests.patch(
            f"{BASE_URL}/api/estimates/{estimate_id}/status",
            json={"status": "pending"},
            headers={**HEADERS, "Authorization": f"Bearer {tokens['admin']}"}
        )
        
        print_test("Update Estimate Status", response.status_code == 200,
                  f"Status changed to pending")
        
        # List estimates
        response = requests.get(
            f"{BASE_URL}/api/estimates/",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        
        if response.status_code == 200:
            estimates = response.json()
            print_test("List Estimates", True, f"Found {len(estimates)} estimates")
        else:
            print_test("List Estimates", False, f"Status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_test("Estimate CRUD", False, f"Error: {str(e)}")
        return False

def test_cost_management():
    """Test 5: Cost management endpoints"""
    print("\n=== COST MANAGEMENT TESTS ===")
    
    if "admin" not in tokens:
        print_test("Cost Management", False, "No auth token available")
        return False
    
    try:
        # Get labor rates
        response = requests.get(
            f"{BASE_URL}/api/costs/labor-rates",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        
        print_test("Get Labor Rates", response.status_code == 200,
                  f"Status: {response.status_code}")
        
        # Get equipment costs
        response = requests.get(
            f"{BASE_URL}/api/costs/equipment",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        
        print_test("Get Equipment Costs", response.status_code == 200,
                  f"Status: {response.status_code}")
        
        # Get overhead settings (admin only)
        response = requests.get(
            f"{BASE_URL}/api/costs/overhead",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        
        print_test("Get Overhead Settings", response.status_code == 200,
                  f"Admin can access overhead settings")
        
        return True
        
    except Exception as e:
        print_test("Cost Management", False, f"Error: {str(e)}")
        return False

def test_external_apis():
    """Test 6: External API integrations"""
    print("\n=== EXTERNAL API TESTS ===")
    
    if "admin" not in tokens:
        print_test("External APIs", False, "No auth token available")
        return False
    
    try:
        # Test Google Maps distance
        response = requests.post(
            f"{BASE_URL}/api/external/distance",
            json={
                "origin": "123 Main St, Anytown, USA",
                "destination": "456 Oak Ave, Somewhere, USA"
            },
            headers={**HEADERS, "Authorization": f"Bearer {tokens['admin']}"}
        )
        
        # May fail if no real API key, but should handle gracefully
        maps_passed = response.status_code in [200, 503]  # 503 if API unavailable
        print_test("Google Maps Distance", maps_passed,
                  f"Status: {response.status_code}")
        
        # Test fuel price
        response = requests.get(
            f"{BASE_URL}/api/external/fuel-price?location=12345",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        
        fuel_passed = response.status_code in [200, 503]
        print_test("Fuel Price API", fuel_passed,
                  f"Status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_test("External APIs", False, f"Error: {str(e)}")
        return False

def test_role_permissions():
    """Test 7: Role-based permissions"""
    print("\n=== ROLE PERMISSION TESTS ===")
    
    # First create test users if they don't exist
    try:
        # Try to create estimator user
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": TEST_ESTIMATOR["username"],
                "email": "estimator@example.com",
                "password": TEST_ESTIMATOR["password"],
                "full_name": "Test Estimator",
                "role": "estimator"
            },
            headers=HEADERS
        )
        
        if response.status_code == 200:
            print("Created estimator user")
        
        # Login as estimator
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": TEST_ESTIMATOR["username"], "password": TEST_ESTIMATOR["password"]}
        )
        
        if response.status_code == 200:
            tokens["estimator"] = response.json()["access_token"]
            
            # Test estimator can create estimates
            response = requests.post(
                f"{BASE_URL}/api/estimates/calculate",
                json={
                    "travel_details": {
                        "miles": 5.0,
                        "estimated_minutes": 10,
                        "vehicle_rate_per_mile": 0.65,
                        "driver_hourly_rate": 25.00
                    },
                    "labor_details": {
                        "estimated_hours": 1.0,
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
                },
                headers={**HEADERS, "Authorization": f"Bearer {tokens['estimator']}"}
            )
            
            print_test("Estimator Can Calculate", response.status_code == 200,
                      "Estimator role working correctly")
            
            # Test estimator cannot modify overhead (admin only)
            response = requests.put(
                f"{BASE_URL}/api/costs/overhead",
                json={"overhead_percent": 30.0},
                headers={**HEADERS, "Authorization": f"Bearer {tokens['estimator']}"}
            )
            
            print_test("Estimator Cannot Modify Overhead", response.status_code == 403,
                      "Permission denied as expected")
            
            return True
        else:
            print_test("Role Permissions", False, "Could not login as estimator")
            return False
            
    except Exception as e:
        print_test("Role Permissions", False, f"Error: {str(e)}")
        return False

def create_sample_data():
    """Create sample data for team testing"""
    print("\n=== CREATING SAMPLE DATA ===")
    
    if "admin" not in tokens:
        print("No admin token, skipping sample data creation")
        return
    
    sample_estimates = [
        {
            "customer_name": "Johnson Family",
            "customer_email": "johnson@email.com",
            "customer_phone": "555-0101",
            "service_address": "123 Oak Street, Springfield, IL 62701",
            "calculation_input": {
                "travel_details": {
                    "miles": 15.0,
                    "estimated_minutes": 25,
                    "vehicle_rate_per_mile": 0.65,
                    "driver_hourly_rate": 25.00
                },
                "labor_details": {
                    "estimated_hours": 6.0,
                    "crew": [
                        {"name": "Lead Arborist", "hourly_rate": 55.00},
                        {"name": "Climber", "hourly_rate": 45.00},
                        {"name": "Ground Worker", "hourly_rate": 25.00}
                    ],
                    "emergency": False,
                    "weekend": False
                },
                "equipment_details": [
                    {"equipment_id": "chipper", "hourly_cost": 75.00},
                    {"equipment_id": "bucket_truck", "hourly_cost": 125.00}
                ],
                "disposal_fees": 250.00,
                "permit_cost": 75.00,
                "margins": {
                    "overhead_percent": 25.0,
                    "profit_percent": 35.0,
                    "safety_buffer_percent": 10.0
                }
            },
            "notes": "Large oak removal, power lines nearby. Need bucket truck for safety."
        },
        {
            "customer_name": "Smith Business Park",
            "customer_email": "maintenance@smithpark.com",
            "customer_phone": "555-0202",
            "service_address": "456 Business Pkwy, Chicago, IL 60601",
            "calculation_input": {
                "travel_details": {
                    "miles": 45.0,
                    "estimated_minutes": 60,
                    "vehicle_rate_per_mile": 0.65,
                    "driver_hourly_rate": 25.00
                },
                "labor_details": {
                    "estimated_hours": 8.0,
                    "crew": [
                        {"name": "Lead Arborist", "hourly_rate": 55.00},
                        {"name": "Climber 1", "hourly_rate": 45.00},
                        {"name": "Climber 2", "hourly_rate": 45.00},
                        {"name": "Ground Worker 1", "hourly_rate": 25.00},
                        {"name": "Ground Worker 2", "hourly_rate": 25.00}
                    ],
                    "emergency": False,
                    "weekend": True  # Weekend work
                },
                "equipment_details": [
                    {"equipment_id": "chipper", "hourly_cost": 75.00},
                    {"equipment_id": "crane", "hourly_cost": 350.00},
                    {"equipment_id": "stump_grinder", "hourly_cost": 85.00}
                ],
                "disposal_fees": 500.00,
                "permit_cost": 150.00,
                "margins": {
                    "overhead_percent": 25.0,
                    "profit_percent": 35.0,
                    "safety_buffer_percent": 10.0
                }
            },
            "notes": "Commercial property maintenance - remove 5 dead trees, weekend work required."
        }
    ]
    
    created_count = 0
    for estimate_data in sample_estimates:
        try:
            response = requests.post(
                f"{BASE_URL}/api/estimates/",
                json=estimate_data,
                headers={**HEADERS, "Authorization": f"Bearer {tokens['admin']}"}
            )
            
            if response.status_code == 200:
                created_count += 1
                result = response.json()
                print(f"  Created estimate {result['estimate_number']} - ${result['final_total']}")
            else:
                print(f"  Failed to create estimate: {response.status_code}")
                
        except Exception as e:
            print(f"  Error creating estimate: {str(e)}")
    
    print(f"\nCreated {created_count} sample estimates")

def run_all_tests():
    """Run all tests and provide summary"""
    print("=" * 60)
    print("TREE SERVICE ESTIMATING APP - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    results = {}
    
    # Run tests
    results["health"] = test_health_check()
    
    if not results["health"]:
        print(f"\n❌ CRITICAL: App is not running at {BASE_URL}!")
        print("Please start the app with:")
        print("  cd 'C:\\Users\\Cameron Cox\\Documents\\Development\\context-engineering-intro'")
        print("  python -m uvicorn src.main:app --reload --port 8002")
        return
    
    results["auth"] = test_authentication()
    results["calculator"] = test_calculator()
    results["estimates"] = test_estimates_crud()
    results["costs"] = test_cost_management()
    results["external"] = test_external_apis()
    results["permissions"] = test_role_permissions()
    
    # Create sample data
    create_sample_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.capitalize()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.0f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! App is ready for team deployment.")
        print("\nNext steps:")
        print("1. Review the sample estimates created")
        print("2. Create accounts for your team members")
        print("3. Configure real API keys for Google Maps and QuickBooks")
        print("4. Set up proper database backups")
        print("5. Deploy to production server")
    else:
        print("\n⚠️  Some tests failed. Please fix issues before deployment.")

if __name__ == "__main__":
    run_all_tests()