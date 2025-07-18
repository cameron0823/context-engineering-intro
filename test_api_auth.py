#!/usr/bin/env python3
"""
Test script demonstrating API authentication and external API usage.
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

async def test_api_flow():
    """Test complete API flow with authentication."""
    async with httpx.AsyncClient() as client:
        print("=== Tree Service Estimating API Test ===\n")
        
        # 1. Test health endpoint (no auth required)
        print("1. Testing health endpoint...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")
        
        # 2. Register a new user
        print("2. Registering a new user...")
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "phone": "+1234567890"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/auth/register", json=user_data)
            if response.status_code == 200:
                print(f"   ✅ User registered successfully!")
                user_response = response.json()
                print(f"   User ID: {user_response['id']}")
                print(f"   Username: {user_response['username']}")
            else:
                print(f"   ❌ Registration failed: {response.status_code}")
                print(f"   Error: {response.json()}")
        except Exception as e:
            print(f"   ❌ Registration error: {e}")
        
        # 3. Login to get access token
        print("\n3. Logging in...")
        login_data = {
            "username": "testuser",
            "password": "SecurePassword123!",
            "grant_type": "password"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Login successful!")
            token_response = response.json()
            access_token = token_response["access_token"]
            print(f"   Token type: {token_response['token_type']}")
            print(f"   Access token: {access_token[:20]}...")
            
            # Set authorization header for subsequent requests
            auth_headers = {"Authorization": f"Bearer {access_token}"}
            
            # 4. Test external API health with authentication
            print("\n4. Testing external API health (with auth)...")
            response = await client.get(
                f"{BASE_URL}/api/external/health",
                headers=auth_headers
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
            
            # 5. Test Google Maps distance calculation
            print("\n5. Testing Google Maps distance calculation...")
            distance_data = {
                "origin": "1600 Amphitheatre Parkway, Mountain View, CA",
                "destination": "1 Infinite Loop, Cupertino, CA"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/external/distance",
                json=distance_data,
                headers=auth_headers
            )
            
            if response.status_code == 200:
                print(f"   ✅ Distance calculated!")
                distance_response = response.json()
                print(f"   Distance: {distance_response['distance_miles']} miles")
                print(f"   Duration: {distance_response['duration_minutes']} minutes")
                print(f"   Distance text: {distance_response['distance_text']}")
                print(f"   Duration text: {distance_response['duration_text']}")
            else:
                print(f"   ❌ Distance calculation failed: {response.status_code}")
                print(f"   Error: {response.json()}")
            
            # 6. Test batch distance calculation
            print("\n6. Testing batch distance calculation...")
            batch_data = {
                "origin": "1600 Amphitheatre Parkway, Mountain View, CA",
                "destinations": [
                    "1 Infinite Loop, Cupertino, CA",
                    "1 Hacker Way, Menlo Park, CA",
                    "345 Spear Street, San Francisco, CA"
                ]
            }
            
            response = await client.post(
                f"{BASE_URL}/api/external/distance/batch",
                json=batch_data,
                headers=auth_headers
            )
            
            if response.status_code == 200:
                print(f"   ✅ Batch distances calculated!")
                batch_response = response.json()
                for i, distance in enumerate(batch_response):
                    print(f"   Destination {i+1}: {distance['distance_miles']} miles, "
                          f"{distance['duration_minutes']} minutes")
            else:
                print(f"   ❌ Batch calculation failed: {response.status_code}")
                print(f"   Error: {response.json()}")
            
            # 7. Test fuel price lookup
            print("\n7. Testing fuel price lookup...")
            response = await client.get(
                f"{BASE_URL}/api/external/fuel-price?location=local&fuel_type=regular",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                print(f"   ✅ Fuel price retrieved!")
                fuel_response = response.json()
                print(f"   Price: ${fuel_response['price_per_gallon']} per gallon")
                print(f"   Fuel type: {fuel_response['fuel_type']}")
                print(f"   Location: {fuel_response['location']}")
                print(f"   Source: {fuel_response['source']}")
            else:
                print(f"   ❌ Fuel price lookup failed: {response.status_code}")
                print(f"   Error: {response.json()}")
                
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Error: {response.json()}")
        
        print("\n✅ API test completed!")


def main():
    """Run the API test flow."""
    asyncio.run(test_api_flow())


if __name__ == "__main__":
    main()