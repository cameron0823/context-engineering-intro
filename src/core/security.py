"""
Security utilities for JWT token generation/validation and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
import secrets

from src.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityService:
    """Service for handling security operations."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            data: Data to encode in the token
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # Unique token ID for revocation
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
            
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise JWTError(f"Could not validate token: {str(e)}")
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def generate_password_reset_token(email: str) -> str:
        """
        Generate a password reset token.
        
        Args:
            email: User's email address
            
        Returns:
            Password reset token
        """
        delta = timedelta(hours=1)  # Reset token valid for 1 hour
        to_encode = {
            "sub": email,
            "type": "password_reset"
        }
        return SecurityService.create_access_token(data=to_encode, expires_delta=delta)
    
    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """
        Verify a password reset token.
        
        Args:
            token: Password reset token
            
        Returns:
            Email address if valid, None otherwise
        """
        try:
            payload = SecurityService.decode_token(token)
            if payload.get("type") != "password_reset":
                return None
            email: str = payload.get("sub")
            return email
        except (JWTError, ValidationError):
            return None
    
    @staticmethod
    def generate_email_verification_token(email: str) -> str:
        """
        Generate an email verification token.
        
        Args:
            email: User's email address
            
        Returns:
            Email verification token
        """
        delta = timedelta(days=7)  # Verification token valid for 7 days
        to_encode = {
            "sub": email,
            "type": "email_verification"
        }
        return SecurityService.create_access_token(data=to_encode, expires_delta=delta)
    
    @staticmethod
    def verify_email_verification_token(token: str) -> Optional[str]:
        """
        Verify an email verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            Email address if valid, None otherwise
        """
        try:
            payload = SecurityService.decode_token(token)
            if payload.get("type") != "email_verification":
                return None
            email: str = payload.get("sub")
            return email
        except (JWTError, ValidationError):
            return None


# Create instance for convenience
security = SecurityService()