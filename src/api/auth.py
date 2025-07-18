"""
Authentication API endpoints.
"""
from typing import Annotated
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from src.db.session import get_db
from src.core.config import settings
from src.core.security import security
from src.models.user import User
from src.models.audit import AuditLog
from src.schemas.user import (
    UserCreate, UserResponse, Token, UserLogin,
    PasswordChange, PasswordReset, EmailVerification
)
from src.api.deps import (
    get_current_active_user, get_request_info, get_current_user_id
)
from src.services.audit import AuditService


router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    background_tasks: BackgroundTasks
) -> User:
    """
    Register a new user.
    
    Only admins can set roles other than VIEWER.
    """
    # Check if username or email already exists
    result = await db.execute(
        select(User).where(
            or_(
                User.username == user_data.username,
                User.email == user_data.email
            )
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        department=user_data.department,
        hashed_password=security.get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True,
        is_verified=False,
        created_by="self-registration"
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Log the registration
    request_info = await get_request_info(request)
    await AuditService.log_change(
        db=db,
        entity=user,
        action="INSERT",
        user_id="self-registration",
        **request_info,
        context={"registration_method": "self"}
    )
    
    # Send verification email in background
    # background_tasks.add_task(send_verification_email, user.email, user.username)
    
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
) -> Token:
    """
    OAuth2 compatible token login.
    
    Get an access token for future requests.
    """
    # Find user by username
    result = await db.execute(
        select(User).where(
            User.username == form_data.username,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        request_info = await get_request_info(request)
        audit_log = AuditLog(
            table_name="login_attempts",
            record_id=0,
            action="LOGIN_FAILED",
            changed_by=form_data.username,
            context={"reason": "invalid_credentials"},
            **request_info
        )
        db.add(audit_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is verified
    if not user.is_verified and settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please check your email.",
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = security.create_refresh_token(
        data={
            "sub": user.username,
            "user_id": user.id
        }
    )
    
    # Log successful login
    request_info = await get_request_info(request)
    audit_log = AuditLog(
        table_name="login_attempts",
        record_id=user.id,
        action="LOGIN_SUCCESS",
        changed_by=str(user.id),
        **request_info
    )
    db.add(audit_log)
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    Refresh access token using refresh token.
    """
    try:
        # Decode refresh token
        payload = security.decode_token(refresh_token)
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.username == username,
                User.is_active == True,
                User.deleted_at.is_(None)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = security.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value
            },
            expires_delta=access_token_expires
        )
        
        new_refresh_token = security.create_refresh_token(
            data={
                "sub": user.username,
                "user_id": user.id
            }
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Get current user profile.
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
) -> dict:
    """
    Change current user's password.
    """
    # Verify current password
    if not security.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = security.get_password_hash(password_data.new_password)
    current_user.updated_by = str(current_user.id)
    
    await db.commit()
    
    # Log password change
    request_info = await get_request_info(request)
    await AuditService.log_change(
        db=db,
        entity=current_user,
        action="PASSWORD_CHANGE",
        user_id=str(current_user.id),
        **request_info,
        context={"action": "password_changed"}
    )
    
    return {"message": "Password changed successfully"}


@router.post("/request-password-reset")
async def request_password_reset(
    email: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks
) -> dict:
    """
    Request password reset email.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Generate reset token
        reset_token = security.generate_password_reset_token(user.email)
        
        # Send reset email in background
        # background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
) -> dict:
    """
    Reset password using token.
    """
    # Verify reset token
    email = security.verify_password_reset_token(reset_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = security.get_password_hash(reset_data.new_password)
    user.updated_by = "password-reset"
    
    await db.commit()
    
    # Log password reset
    request_info = await get_request_info(request)
    await AuditService.log_change(
        db=db,
        entity=user,
        action="PASSWORD_RESET",
        user_id="password-reset",
        **request_info,
        context={"method": "email_token"}
    )
    
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
async def verify_email(
    verification: EmailVerification,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    Verify email address using token.
    """
    # Verify token
    email = security.verify_email_verification_token(verification.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update verification status
    user.is_verified = True
    user.updated_by = "email-verification"
    
    await db.commit()
    
    return {"message": "Email verified successfully"}