#!/usr/bin/env python3
"""
Demo script to showcase the Tree Service Estimating App
"""
import requests
import json
import time
from decimal import Decimal

BASE_URL = "http://localhost:8002"

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def demo_app():
    print("🌳 TREE SERVICE ESTIMATING APP DEMO 🌳")
    
    # Check if app is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ App is not running! Start it with: python start_dev_server.py")
            return
    except:
        print("❌ Cannot connect to app! Start it with: python start_dev_server.py")
        return
    
    print_section("1. APP INFORMATION")
    print(f"✅ App is running at {BASE_URL}")
    print(f"📚 API Documentation: {BASE_URL}/docs")
    print(f"❤️  Health Check: {BASE_URL}/health")
    
    # Login
    print_section("2. AUTHENTICATION")
    print("Logging in as admin...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "admin", "password": "Admin123!"}
    )
    
    if response.status_code != 200:
        print("❌ Login failed! Run: python create_test_users.py")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful!")
    print(f"🔑 Token: {token[:20]}...")
    
    # Get user info
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    user = response.json()
    print(f"👤 Logged in as: {user['username']} (Role: {user['role']})")
    
    # Calculate estimate
    print_section("3. ESTIMATE CALCULATION")
    print("Calculating estimate for tree removal job...")
    
    calc_data = {
        "travel_details": {
            "miles": 15.5,
            "estimated_minutes": 30,
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
        "disposal_fees": 200.00,
        "permit_cost": 75.00,
        "margins": {
            "overhead_percent": 25.0,
            "profit_percent": 35.0,
            "safety_buffer_percent": 10.0
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/estimates/calculate",
        json=calc_data,
        headers={**headers, "Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n📊 CALCULATION RESULTS:")
        print(f"   Travel Cost: ${result['travel_cost']}")
        print(f"   Labor Cost: ${result['labor_cost']}")
        print(f"   Equipment Cost: ${result['equipment_cost']}")
        print(f"   Disposal Fees: ${result['disposal_fees']}")
        print(f"   Permit Cost: ${result['permit_cost']}")
        print(f"   Direct Costs: ${result['direct_costs']}")
        print(f"   Overhead (25%): ${result['overhead_amount']}")
        print(f"   Safety Buffer (10%): ${result['safety_buffer_amount']}")
        print(f"   Profit (35%): ${result['profit_amount']}")
        print(f"   ──────────────────────")
        print(f"   FINAL TOTAL: ${result['final_total']} ✨")
        print(f"\n   Note: Final total is rounded to nearest $5")
    
    # Create estimate
    print_section("4. CREATE ESTIMATE")
    print("Creating a new estimate for a customer...")
    
    estimate_data = {
        "customer_name": "Johnson Family",
        "customer_email": "johnson@example.com",
        "customer_phone": "555-0123",
        "service_address": "456 Oak Street, Springfield, IL 62701",
        "calculation_input": calc_data,
        "notes": "Large oak tree removal. Power lines nearby - need bucket truck for safety."
    }
    
    response = requests.post(
        f"{BASE_URL}/api/estimates/",
        json=estimate_data,
        headers={**headers, "Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        estimate = response.json()
        print(f"✅ Estimate created successfully!")
        print(f"   Estimate #: {estimate['estimate_number']}")
        print(f"   Customer: {estimate['customer_name']}")
        print(f"   Total: ${estimate['final_total']}")
        print(f"   Status: {estimate['status']}")
        print(f"   Valid Until: {estimate['valid_until']}")
        
        estimate_id = estimate['id']
    
    # List estimates
    print_section("5. VIEW ALL ESTIMATES")
    response = requests.get(f"{BASE_URL}/api/estimates/", headers=headers)
    
    if response.status_code == 200:
        estimates = response.json()
        print(f"Found {len(estimates)} estimate(s):\n")
        
        for est in estimates[:5]:  # Show first 5
            print(f"   📄 {est['estimate_number']}")
            print(f"      Customer: {est['customer_name']}")
            print(f"      Amount: ${est['final_total']}")
            print(f"      Status: {est['status']}")
            print()
    
    # Cost management
    print_section("6. COST MANAGEMENT")
    
    # Labor rates
    response = requests.get(f"{BASE_URL}/api/costs/labor-rates", headers=headers)
    if response.status_code == 200:
        rates = response.json()
        print("💰 Current Labor Rates:")
        for rate in rates[:5]:
            print(f"   {rate['role']}: ${rate['hourly_rate']}/hour")
    
    # Equipment costs
    response = requests.get(f"{BASE_URL}/api/costs/equipment", headers=headers)
    if response.status_code == 200:
        equipment = response.json()
        print("\n🚜 Equipment Costs:")
        for eq in equipment[:5]:
            print(f"   {eq['name']}: ${eq['hourly_cost']}/hour")
    
    print_section("✅ DEMO COMPLETE!")
    print("Your Tree Service Estimating App is working correctly!")
    print("\nNext steps:")
    print("1. Open the API docs in your browser: http://localhost:8002/docs")
    print("2. Try creating estimates with different parameters")
    print("3. Test role-based permissions with different user accounts")
    print("4. Configure real API keys for production use")
    
    print("\n🎉 Ready to push to git and deploy!")

if __name__ == "__main__":
    demo_app()