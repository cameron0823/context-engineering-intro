#!/usr/bin/env python3
"""
Complete test suite for Tree Service Estimating App
Handles database setup and comprehensive testing
"""
import os
import sys
import time
import requests
import subprocess
import signal
import asyncio
from pathlib import Path

# Configuration
SERVER_PORT = 8002
BASE_URL = f"http://localhost:{SERVER_PORT}"
DB_FILE = "treeservice_test.db"

# Set up test environment
os.environ["DATABASE_URL"] = f"sqlite:///./{DB_FILE}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "True"
os.environ["GOOGLE_MAPS_API_KEY"] = "test-key"
os.environ["QUICKBOOKS_CLIENT_ID"] = "test-id"
os.environ["QUICKBOOKS_CLIENT_SECRET"] = "test-secret"
os.environ["QUICKBOOKS_COMPANY_ID"] = "test-company"
os.environ["FUEL_API_KEY"] = "test-fuel-key"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"


def cleanup_database():
    """Remove existing test database"""
    if Path(DB_FILE).exists():
        print(f"Removing existing database: {DB_FILE}")
        os.remove(DB_FILE)


async def setup_database():
    """Set up fresh database with tables and test data"""
    from src.db.session import engine, Base, async_session_maker
    from src.models.user import User, UserRole
    from src.models.costs import LaborRate, EquipmentCost, OverheadSettings
    from src.core.security import security
    from datetime import datetime
    from decimal import Decimal
    
    print("Creating database tables...")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test users
    async with async_session_maker() as session:
        users = [
            User(
                username="admin",
                email="admin@test.com",
                full_name="Test Admin",
                hashed_password=security.get_password_hash("Admin123!"),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                created_by="system"
            ),
            User(
                username="estimator",
                email="estimator@test.com",
                full_name="Test Estimator",
                hashed_password=security.get_password_hash("Estimator123!"),
                role=UserRole.ESTIMATOR,
                is_active=True,
                is_verified=True,
                created_by="system"
            )
        ]
        
        for user in users:
            session.add(user)
        
        # Add labor rates
        labor_rates = [
            LaborRate(
                role="Lead Arborist",
                hourly_rate=Decimal("55.00"),
                category="skilled",
                effective_date=datetime.utcnow().date(),
                created_by="system"
            ),
            LaborRate(
                role="Ground Worker",
                hourly_rate=Decimal("25.00"),
                category="general",
                effective_date=datetime.utcnow().date(),
                created_by="system"
            )
        ]
        
        for rate in labor_rates:
            session.add(rate)
        
        # Add equipment
        equipment = [
            EquipmentCost(
                name="Wood Chipper",
                equipment_id="chipper",
                hourly_cost=Decimal("75.00"),
                category="processing",
                is_available=True,
                effective_date=datetime.utcnow().date(),
                created_by="system"
            )
        ]
        
        for eq in equipment:
            session.add(eq)
        
        # Add overhead settings
        overhead = OverheadSettings(
            overhead_percent=Decimal("25.0"),
            profit_percent=Decimal("35.0"),
            safety_buffer_percent=Decimal("10.0"),
            vehicle_rate_per_mile=Decimal("0.65"),
            driver_hourly_rate=Decimal("25.00"),
            effective_date=datetime.utcnow().date(),
            created_by="system"
        )
        session.add(overhead)
        
        await session.commit()
    
    await engine.dispose()
    print("✅ Database setup complete")


def start_server():
    """Start the FastAPI server"""
    print("\nStarting server...")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.main:app",
        "--port",
        str(SERVER_PORT),
        "--reload"
    ]
    process = subprocess.Popen(cmd, cwd=Path(__file__).parent)
    
    # Wait for server to start
    for i in range(10):
        time.sleep(1)
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("✅ Server started successfully")
                return process
        except:
            pass
    
    print("❌ Server failed to start")
    process.terminate()
    return None


def run_tests():
    """Run comprehensive tests"""
    print("\n" + "=" * 60)
    print("RUNNING COMPREHENSIVE TESTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        test_passed = response.status_code == 200
        results.append(("Health Check", test_passed))
        print(f"\n1. Health Check: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    except Exception as e:
        results.append(("Health Check", False))
        print(f"\n1. Health Check: ❌ FAILED - {str(e)}")
    
    # Test 2: Authentication
    try:
        # Login
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            
            # Verify token
            response = requests.get(
                f"{BASE_URL}/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            test_passed = response.status_code == 200
            results.append(("Authentication", test_passed))
            print(f"\n2. Authentication: {'✅ PASSED' if test_passed else '❌ FAILED'}")
            
            # Store token for other tests
            auth_header = {"Authorization": f"Bearer {token}"}
        else:
            results.append(("Authentication", False))
            print(f"\n2. Authentication: ❌ FAILED - {response.text}")
            auth_header = {}
    except Exception as e:
        results.append(("Authentication", False))
        print(f"\n2. Authentication: ❌ FAILED - {str(e)}")
        auth_header = {}
    
    # Test 3: Calculator
    if auth_header:
        try:
            calc_data = {
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
            }
            
            response = requests.post(
                f"{BASE_URL}/api/estimates/calculate",
                json=calc_data,
                headers={**auth_header, "Content-Type": "application/json"}
            )
            
            test_passed = response.status_code == 200
            if test_passed:
                result = response.json()
                print(f"\n3. Calculator: ✅ PASSED - Total: ${result.get('final_total', 0)}")
            else:
                print(f"\n3. Calculator: ❌ FAILED - {response.text}")
            
            results.append(("Calculator", test_passed))
        except Exception as e:
            results.append(("Calculator", False))
            print(f"\n3. Calculator: ❌ FAILED - {str(e)}")
    
    # Test 4: Estimates CRUD
    if auth_header:
        try:
            # Create estimate
            estimate_data = {
                "customer_name": "Test Customer",
                "customer_email": "test@example.com",
                "customer_phone": "555-0123",
                "service_address": "123 Test St",
                "calculation_input": calc_data,
                "notes": "Test estimate"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/estimates/",
                json=estimate_data,
                headers={**auth_header, "Content-Type": "application/json"}
            )
            
            test_passed = response.status_code == 200
            if test_passed:
                estimate = response.json()
                print(f"\n4. Estimate CRUD: ✅ PASSED - Created: {estimate.get('estimate_number', 'N/A')}")
            else:
                print(f"\n4. Estimate CRUD: ❌ FAILED - {response.text}")
            
            results.append(("Estimate CRUD", test_passed))
        except Exception as e:
            results.append(("Estimate CRUD", False))
            print(f"\n4. Estimate CRUD: ❌ FAILED - {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, passed in results:
        print(f"{test_name}: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! App is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Please check the logs.")
    
    return passed == total


async def main():
    """Main test runner"""
    print("Tree Service Estimating App - Complete Test Suite")
    print("=" * 60)
    
    # Clean up
    cleanup_database()
    
    # Set up database
    await setup_database()
    
    # Start server
    server_process = start_server()
    if not server_process:
        print("Failed to start server")
        return
    
    try:
        # Run tests
        time.sleep(2)  # Give server time to fully initialize
        all_passed = run_tests()
        
        if all_passed:
            print("\n✅ Your app is ready for team use!")
            print("\nNext steps:")
            print("1. Update .env with production database and API keys")
            print("2. Run migrations on production database")
            print("3. Create user accounts for your team")
            print("4. Deploy to production server")
        
    finally:
        # Clean up
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())