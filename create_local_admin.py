"""
Quick script to create an admin account using local backend
Run this with your backend running locally
"""
import requests
import json

print("=" * 60)
print("LOCAL ADMIN ACCOUNT CREATION")
print("=" * 60)
print("\nThis will create an admin account using your LOCAL backend.")
print("Make sure your backend is running locally first!\n")

# Local API URL
API_URL = "http://localhost:8000/api"

# Admin account details
ADMIN_USER = {
    "username": "admin",
    "email": "admin@coxtreeservice.com", 
    "password": "AdminPass123!",
    "full_name": "System Administrator",
    "role": "admin"
}

def test_local_connection():
    """Test if local backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✓ Local backend is running!")
            return True
    except:
        pass
    return False

def create_admin():
    """Create the admin account"""
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json=ADMIN_USER,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"\n✅ SUCCESS! Admin account created!")
            print("\n" + "="*40)
            print("ADMIN LOGIN DETAILS:")
            print("="*40)
            print(f"Username: {ADMIN_USER['username']}")
            print(f"Password: {ADMIN_USER['password']}")
            print("\nLogin at: http://localhost:3000/admin")
            print("(or wherever your frontend is running)")
            print("="*40)
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print(f"\n✓ Admin account already exists!")
            print("\n" + "="*40)
            print("EXISTING ADMIN LOGIN:")
            print("="*40)
            print(f"Username: {ADMIN_USER['username']}")
            print(f"Password: {ADMIN_USER['password']}")
            print("="*40)
            return True
        else:
            print(f"\n❌ Failed to create admin: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    # Check if backend is running
    if not test_local_connection():
        print("\n❌ LOCAL BACKEND NOT RUNNING!")
        print("\nTo start your backend locally:")
        print("1. Open a new terminal")
        print("2. Navigate to: C:\\Users\\Cameron Cox\\Documents\\Development\\context-engineering-intro")
        print("3. Run: uvicorn src.main:app --reload")
        print("4. Then run this script again")
        return
    
    # Create admin account
    create_admin()
    
    print("\n💡 NEXT STEPS:")
    print("1. Your frontend at https://cox-tree-quote-app.web.app")
    print("   is configured for the Railway backend")
    print("2. To use it with your LOCAL backend, you'll need to")
    print("   temporarily update the API URL in the browser console")
    print("3. OR access the frontend locally if you have it running")

if __name__ == "__main__":
    main()