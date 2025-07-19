"""
Complete setup script for Cox Tree Service App
This will create users and configure the system
"""
import requests
import json
import time

# Your Railway API URL
API_URL = "https://context-engineering-intro-production.up.railway.app/api"

# Test users to create
INITIAL_USERS = [
    {
        "username": "admin",
        "email": "admin@coxtreeservice.com",
        "password": "AdminPass123!",
        "full_name": "System Administrator",
        "role": "admin"
    },
    {
        "username": "cameron",
        "email": "cameron@coxtreeservice.com",
        "password": "CoxTree2024!",
        "full_name": "Cameron Cox",
        "role": "admin"
    },
    {
        "username": "manager1",
        "email": "manager@coxtreeservice.com",
        "password": "Manager123!",
        "full_name": "Office Manager",
        "role": "manager"
    },
    {
        "username": "estimator1",
        "email": "estimator1@coxtreeservice.com",
        "password": "Estimator123!",
        "full_name": "Field Estimator 1",
        "role": "estimator"
    },
    {
        "username": "estimator2",
        "email": "estimator2@coxtreeservice.com",
        "password": "Estimator123!",
        "full_name": "Field Estimator 2",
        "role": "estimator"
    }
]

def test_api_connection():
    """Test if the API is accessible"""
    print(f"Testing connection to {API_URL}...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API is accessible!")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Could not connect to API: {e}")
        return False

def create_initial_users():
    """Create the initial user accounts"""
    print("\nCreating initial users...")
    
    # First, try to create the admin user via registration endpoint
    for user in INITIAL_USERS:
        print(f"\nCreating user: {user['username']}...")
        
        # Try to register the user
        try:
            response = requests.post(
                f"{API_URL}/api/auth/register",
                json=user,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✓ Created {user['username']} successfully!")
            elif response.status_code == 400 and "already registered" in response.text:
                print(f"! User {user['username']} already exists")
            else:
                print(f"✗ Failed to create {user['username']}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ Error creating {user['username']}: {e}")

def test_login():
    """Test logging in with the admin account"""
    print("\nTesting admin login...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={
                "username": "admin",
                "password": "AdminPass123!"
            }
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✓ Admin login successful!")
            return token
        else:
            print(f"✗ Admin login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def configure_initial_pricing(token):
    """Set up initial pricing configuration"""
    print("\nConfiguring initial pricing...")
    
    pricing_data = {
        "labor_rates": {
            "climber": 45.00,
            "groundsman": 25.00,
            "driver": 25.00
        },
        "overhead_percent": 25.0,
        "profit_percent": 35.0,
        "safety_buffer_percent": 10.0,
        "vehicle_rate_per_mile": 0.65,
        "equipment_rates": {
            "chipper": 75.00,
            "bucket_truck": 125.00,
            "stump_grinder": 85.00
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/costs/",
            json=pricing_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code in [200, 201]:
            print("✓ Pricing configuration saved!")
        else:
            print(f"✗ Failed to save pricing: {response.status_code}")
    except Exception as e:
        print(f"✗ Pricing configuration error: {e}")

def print_team_instructions():
    """Print instructions for the team"""
    print("\n" + "="*60)
    print("COX TREE SERVICE APP - TEAM ACCESS INFORMATION")
    print("="*60)
    print("\n📱 MOBILE APP (Field Estimators):")
    print("URL: https://cox-tree-quote-app.web.app")
    print("\n💼 ADMIN DASHBOARD (Office/Management):")
    print("URL: https://cox-tree-quote-app.web.app/admin")
    print("\n👥 USER ACCOUNTS CREATED:")
    print("-"*40)
    
    for user in INITIAL_USERS:
        role_desc = {
            "admin": "Full System Access",
            "manager": "Approve Estimates, View Reports",
            "estimator": "Create & Edit Estimates"
        }.get(user['role'], user['role'])
        
        print(f"\n{user['full_name']} ({role_desc}):")
        print(f"  Username: {user['username']}")
        print(f"  Password: {user['password']}")
    
    print("\n⚠️  IMPORTANT:")
    print("- Have everyone change their password after first login")
    print("- Mobile users should 'Add to Home Screen' for app-like experience")
    print("- Enable location and camera permissions when prompted")
    print("\n" + "="*60)

def main():
    """Run the complete setup"""
    print("Cox Tree Service App Setup")
    print("="*60)
    
    # Test API connection
    if not test_api_connection():
        print("\n❌ Cannot connect to API. Please check:")
        print(f"1. Is your Railway backend deployed and running?")
        print(f"2. Is the API_URL correct? Currently set to: {API_URL}")
        print(f"3. Update the API_URL in this script with your actual Railway URL")
        return
    
    # Create users
    create_initial_users()
    
    # Test login and get token
    token = test_login()
    
    if token:
        # Configure pricing
        configure_initial_pricing(token)
    
    # Print instructions
    print_team_instructions()
    
    # Save instructions to file
    with open("TEAM_ACCESS_INFO.txt", "w") as f:
        f.write("COX TREE SERVICE APP - TEAM ACCESS INFORMATION\n")
        f.write("="*60 + "\n\n")
        f.write("MOBILE APP: https://cox-tree-quote-app.web.app\n")
        f.write("ADMIN DASHBOARD: https://cox-tree-quote-app.web.app/admin\n\n")
        f.write("USER ACCOUNTS:\n")
        f.write("-"*40 + "\n")
        for user in INITIAL_USERS:
            f.write(f"\n{user['full_name']}:\n")
            f.write(f"  Username: {user['username']}\n")
            f.write(f"  Password: {user['password']}\n")
            f.write(f"  Role: {user['role']}\n")
    
    print("\n✓ Team access information saved to TEAM_ACCESS_INFO.txt")
    print("\n🎉 Setup complete! Your team can now start using the app.")

if __name__ == "__main__":
    main()