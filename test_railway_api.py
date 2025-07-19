"""
Quick script to test Railway API connection
"""
import requests

# Common Railway URL patterns - try these
POSSIBLE_URLS = [
    "https://tree-api.railway.app",
    "https://context-engineering-intro.railway.app",
    "https://tree-service-api.railway.app",
    "https://cox-tree-api.railway.app"
]

print("Testing possible Railway URLs...\n")

for url in POSSIBLE_URLS:
    try:
        print(f"Trying {url}...")
        response = requests.get(f"{url}/health", timeout=3)
        if response.status_code == 200:
            print(f"✓ SUCCESS! Your API is at: {url}")
            print(f"Response: {response.json()}")
            
            # Test if it's our app
            try:
                root = requests.get(url)
                if "Tree Service" in root.text:
                    print("✓ Confirmed: This is your Tree Service API!")
            except:
                pass
                
            print(f"\nNEXT STEP: Update API_URL in setup_live_app.py to: {url}")
            break
    except:
        print(f"✗ Not accessible")

print("\nIf none worked, check your Railway dashboard for the actual URL.")