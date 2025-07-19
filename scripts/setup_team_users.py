"""
Script to create initial team users via the API.
Run this after the admin user is created.
"""
import requests
import json

# CHANGE THIS TO YOUR ACTUAL RAILWAY API URL
API_URL = "https://your-app.railway.app"  # Update this!

# Initial users to create
TEAM_USERS = [
    {
        "username": "john_estimator",
        "email": "john@coxtreeservice.com",
        "password": "TempPass123!",
        "full_name": "John Smith",
        "role": "estimator"
    },
    {
        "username": "sarah_manager",
        "email": "sarah@coxtreeservice.com", 
        "password": "TempPass123!",
        "full_name": "Sarah Johnson",
        "role": "manager"
    },
    {
        "username": "mike_estimator",
        "email": "mike@coxtreeservice.com",
        "password": "TempPass123!",
        "full_name": "Mike Wilson",
        "role": "estimator"
    },
    {
        "username": "viewer_account",
        "email": "viewer@coxtreeservice.com",
        "password": "TempPass123!",
        "full_name": "View Only User",
        "role": "viewer"
    }
]

def setup_team():
    # First, login as admin
    print("Logging in as admin...")
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        data={
            "username": "admin",
            "password": "ChangeMe123!"  # Use the admin password
        }
    )
    
    if login_response.status_code != 200:
        print("Failed to login as admin!")
        print(login_response.text)
        return
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create each user
    for user in TEAM_USERS:
        print(f"Creating user: {user['username']}...")
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json=user,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✓ Created {user['username']}")
        else:
            print(f"✗ Failed to create {user['username']}: {response.text}")
    
    print("\nTeam setup complete!")
    print("\nUser Roles:")
    print("- Admin: Full system access")
    print("- Manager: Approve estimates, view reports")
    print("- Estimator: Create and edit estimates")
    print("- Viewer: Read-only access")
    print("\nREMINDER: Have all users change their passwords on first login!")

if __name__ == "__main__":
    setup_team()