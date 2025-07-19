"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from jose import jwt

from src.core.config import settings
from src.models.user import User, UserRole
from src.core.security import security


class TestRegistration:
    """Test user registration endpoint."""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "NewPassword123!",
                "full_name": "New User",
                "phone_number": "555-0000",
                "department": "Engineering"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["role"] == "VIEWER"  # Default role
        assert "hashed_password" not in data
    
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate username."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "Password123!",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "Password123!",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "Password123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422  # Validation error
    
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422  # Should fail validation


class TestLogin:
    """Test login endpoint."""
    
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "TestPassword123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token claims
        payload = jwt.decode(
            data["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(test_user.id)
        assert payload["type"] == "access"
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "Password123!"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_login_inactive_user(self, client: AsyncClient, test_db):
        """Test login with inactive user."""
        # Create inactive user
        user = User(
            username="inactive",
            email="inactive@example.com",
            full_name="Inactive User",
            hashed_password=security.get_password_hash("Password123!"),
            is_active=False
        )
        test_db.add(user)
        await test_db.commit()
        
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "inactive",
                "password": "Password123!"
            }
        )
        assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh endpoint."""
    
    async def test_refresh_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "TestPassword123!"
            }
        )
        tokens = login_response.json()
        
        # Use refresh token
        response = await client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != tokens["access_token"]  # New token
    
    async def test_refresh_with_access_token(self, client: AsyncClient, test_user: User):
        """Test refresh with access token (should fail)."""
        # First login to get tokens
        login_response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "TestPassword123!"
            }
        )
        tokens = login_response.json()
        
        # Try to use access token for refresh
        response = await client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]


class TestPasswordManagement:
    """Test password change and reset endpoints."""
    
    async def test_change_password_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful password change."""
        response = await client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "TestPassword123!",
                "new_password": "NewPassword123!"
            }
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
    
    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """Test password change with wrong current password."""
        response = await client.post(
            "/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword123!"
            }
        )
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]
    
    async def test_request_password_reset(self, client: AsyncClient, test_user: User):
        """Test password reset request."""
        response = await client.post(
            "/api/auth/request-password-reset",
            params={"email": test_user.email}
        )
        assert response.status_code == 200
        assert "If an account exists" in response.json()["message"]
    
    async def test_request_password_reset_nonexistent(self, client: AsyncClient):
        """Test password reset for non-existent email."""
        response = await client.post(
            "/api/auth/request-password-reset",
            params={"email": "nonexistent@example.com"}
        )
        # Should return same response to prevent email enumeration
        assert response.status_code == 200
        assert "If an account exists" in response.json()["message"]


class TestUserProfile:
    """Test user profile endpoints."""
    
    async def test_get_current_user(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Test getting current user profile."""
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "hashed_password" not in data
    
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting profile without authentication."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting profile with invalid token."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting on auth endpoints."""
    
    @pytest.mark.skip(reason="Rate limiting tests require special setup")
    async def test_login_rate_limit(self, client: AsyncClient):
        """Test rate limiting on login endpoint."""
        # Make multiple rapid requests
        for i in range(6):  # Rate limit is 5 per minute
            response = await client.post(
                "/api/auth/login",
                data={
                    "username": f"user{i}",
                    "password": "password"
                }
            )
        
        # The 6th request should be rate limited
        assert response.status_code == 429
        assert "rate_limit_exceeded" in response.json()["error"]