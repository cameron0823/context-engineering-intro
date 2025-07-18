#!/bin/bash
# Test Tree Service Estimating API with curl commands

BASE_URL="http://localhost:8001"

echo "=== Tree Service Estimating API Test with Curl ==="
echo

# 1. Test health endpoint
echo "1. Testing health endpoint..."
curl -s $BASE_URL/health | jq '.'
echo

# 2. Register a new user
echo "2. Registering a new user..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User",
    "phone": "+1234567890"
  }')

echo $REGISTER_RESPONSE | jq '.'
echo

# 3. Login to get access token
echo "3. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=SecurePassword123!&grant_type=password")

# Extract the access token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" != "null" ]; then
    echo "✅ Login successful! Token: ${ACCESS_TOKEN:0:20}..."
    echo
    
    # 4. Test external API health with authentication
    echo "4. Testing external API health (with auth)..."
    curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
      $BASE_URL/api/external/health | jq '.'
    echo
    
    # 5. Test Google Maps distance calculation
    echo "5. Testing Google Maps distance calculation..."
    curl -s -X POST $BASE_URL/api/external/distance \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "origin": "1600 Amphitheatre Parkway, Mountain View, CA",
        "destination": "1 Infinite Loop, Cupertino, CA"
      }' | jq '.'
    echo
    
    # 6. Test fuel price lookup
    echo "6. Testing fuel price lookup..."
    curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$BASE_URL/api/external/fuel-price?location=local&fuel_type=regular" | jq '.'
    echo
    
    # 7. Create an estimate (example)
    echo "7. Creating an estimate..."
    ESTIMATE_RESPONSE=$(curl -s -X POST $BASE_URL/api/estimates \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_phone": "+1234567890",
        "customer_address": "123 Main St, Anytown, CA 12345",
        "job_address": "456 Oak Ave, Anytown, CA 12345",
        "job_date": "'$(date -d "+7 days" +%Y-%m-%d)'",
        "job_description": "Remove large oak tree",
        "tree_count": 1,
        "estimated_hours": 4.0,
        "crew_size": 3,
        "equipment_needed": ["Chainsaw", "Chipper", "Truck"],
        "travel_miles": 10.5,
        "disposal_required": true
      }')
    
    echo $ESTIMATE_RESPONSE | jq '.'
    
else
    echo "❌ Login failed!"
    echo $LOGIN_RESPONSE | jq '.'
fi

echo
echo "✅ API test completed!"