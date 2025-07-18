"""
Dependencies for FastAPI endpoints, including authentication and authorization.
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db
from src.core.security import security
from src.models.user import User
from src.schemas.user import TokenData


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        db: Database session
        token: JWT access token
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = security.decode_token(token)
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        # Verify token type
        if payload.get("type") != "access":
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id)
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(
            User.id == token_data.user_id,
            User.username == token_data.username,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


def require_permission(permission: str):
    """
    Dependency to check if user has a specific permission.
    
    Args:
        permission: Permission string to check
        
    Returns:
        Dependency function
    """
    async def check_permission(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    return check_permission


def require_role(role: str):
    """
    Dependency to check if user has a specific role.
    
    Args:
        role: Role name to check
        
    Returns:
        Dependency function
    """
    async def check_role(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' not allowed. Required role: {role}"
            )
        return current_user
    
    return check_role


# Convenience dependencies for common permission checks
require_admin = require_permission("users:write")
require_manager = require_permission("estimates:approve")
require_estimator = require_permission("estimates:write")
require_cost_read = require_permission("costs:read")
require_cost_write = require_permission("costs:write")


async def get_current_user_id(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> str:
    """Get current user ID as string for audit trails."""
    return str(current_user.id)


async def get_request_info(request: Request) -> dict:
    """
    Get request information for audit logging.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with IP address and user agent
    """
    # Get IP address (handle proxy headers)
    ip_address = request.client.host
    if "x-forwarded-for" in request.headers:
        ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        ip_address = request.headers["x-real-ip"]
    
    # Get user agent
    user_agent = request.headers.get("user-agent", "Unknown")
    
    return {
        "ip_address": ip_address,
        "user_agent": user_agent[:500]  # Limit length
    }


class PermissionChecker:
    """
    Class-based dependency for checking multiple permissions.
    """
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions
    
    def __call__(
        self, 
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        for permission in self.required_permissions:
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        return current_user


class RoleChecker:
    """
    Class-based dependency for checking user roles.
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(
        self, 
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' not allowed"
            )
        return current_user


# Pagination dependencies
async def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> dict:
    """
    Get pagination parameters.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with skip and limit
    """
    return {"skip": skip, "limit": min(limit, 1000)}  # Cap at 1000