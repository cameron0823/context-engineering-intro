"""Debug authentication issues."""
import requests

# First, let's see if the API docs are working
print("Checking API documentation...")
response = requests.get("http://localhost:8001/docs")
print(f"API docs status: {response.status_code}")

# Check if login endpoint exists
print("\nChecking login endpoint...")
response = requests.post(
    "http://localhost:8001/api/auth/login",
    data={
        "username": "admin",
        "password": "admin123",
        "grant_type": "password"
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
print(f"Login response status: {response.status_code}")
print(f"Response body: {response.text}")

# If we have server logs, they would show the actual error
print("\nNote: Check the server console for detailed error messages")