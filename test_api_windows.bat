@echo off
REM Test Tree Service Estimating API with curl commands (Windows version)

set BASE_URL=http://localhost:8001

echo === Tree Service Estimating API Test ===
echo.

REM 1. Test health endpoint
echo 1. Testing health endpoint...
curl -s %BASE_URL%/health
echo.
echo.

REM 2. Register a new user
echo 2. Registering a new user...
curl -s -X POST %BASE_URL%/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"testuser\", \"email\": \"testuser@example.com\", \"password\": \"SecurePassword123!\", \"full_name\": \"Test User\", \"phone\": \"+1234567890\"}"
echo.
echo.

REM 3. Login to get access token
echo 3. Logging in...
echo Please copy the access token from the response below:
curl -s -X POST %BASE_URL%/api/auth/login ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=testuser&password=SecurePassword123!&grant_type=password"
echo.
echo.

echo 4. To test authenticated endpoints, use the token like this:
echo    curl -H "Authorization: Bearer YOUR_TOKEN_HERE" %BASE_URL%/api/external/health
echo.
echo Example commands:
echo    - External API health: curl -H "Authorization: Bearer TOKEN" %BASE_URL%/api/external/health
echo    - Fuel price: curl -H "Authorization: Bearer TOKEN" "%BASE_URL%/api/external/fuel-price?location=local&fuel_type=regular"
echo.
pause