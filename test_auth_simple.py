"""
Simple authentication test script.
"""
import asyncio
import httpx
import json

async def test_auth():
    """Test authentication endpoints."""
    base_url = "http://localhost:8001"
    
    # Test health endpoint first
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # Test login with different credentials
        test_users = [
            ("admin@treeservice.com", "admin123"),
            ("admin", "admin123"),
            ("manager@treeservice.com", "manager123"),
            ("estimator@treeservice.com", "estimator123"),
            ("viewer@treeservice.com", "viewer123")
        ]
        
        for username, password in test_users:
            print(f"\nTesting login for: {username}")
            
            # Form data for OAuth2PasswordRequestForm
            form_data = {
                "username": username,
                "password": password,
                "grant_type": "password"  # OAuth2 requires this
            }
            
            try:
                response = await client.post(
                    f"{base_url}/api/auth/login",
                    data=form_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    print(f"✅ Login successful!")
                    print(f"   Access token: {token_data.get('access_token')[:20]}...")
                    
                    # Test authenticated endpoint
                    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                    me_response = await client.get(f"{base_url}/api/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        user_data = me_response.json()
                        print(f"   User info: {user_data['username']} ({user_data['role']})")
                    else:
                        print(f"   ❌ Failed to get user info: {me_response.status_code}")
                else:
                    print(f"❌ Login failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())