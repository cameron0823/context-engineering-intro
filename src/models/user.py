"""
User model with role-based access control.
"""
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class UserRole(str, Enum):
    """User roles with different permission levels."""
    ADMIN = "admin"          # Full access to all features and costs
    MANAGER = "manager"      # Approve quotes, view costs
    ESTIMATOR = "estimator"  # Create quotes, limited cost visibility
    VIEWER = "viewer"        # Read-only access


class User(BaseModel):
    """User model with authentication and role information."""
    __tablename__ = "users"
    
    # Basic information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Role-based access
    role = Column(
        SQLEnum(UserRole), 
        default=UserRole.VIEWER, 
        nullable=False,
        index=True
    )
    
    # Additional fields
    phone_number = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Relationships (will be added as we create other models)
    # estimates = relationship("Estimate", back_populates="created_by_user")
    # audit_logs = relationship("AuditLog", back_populates="user")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_active_role', 'is_active', 'role'),
        Index('idx_user_department', 'department'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission based on their role.
        
        Args:
            permission: Permission string (e.g., "costs:write", "estimates:approve")
            
        Returns:
            True if user has permission, False otherwise
        """
        # Define permission matrix
        permission_matrix = {
            UserRole.ADMIN: [
                "costs:read", "costs:write", "costs:delete",
                "estimates:read", "estimates:write", "estimates:delete", "estimates:approve",
                "users:read", "users:write", "users:delete",
                "reports:read", "reports:write",
                "audit:read",
                "settings:read", "settings:write"
            ],
            UserRole.MANAGER: [
                "costs:read",
                "estimates:read", "estimates:write", "estimates:approve",
                "users:read",
                "reports:read", "reports:write",
                "audit:read"
            ],
            UserRole.ESTIMATOR: [
                "costs:read",  # Limited visibility in API layer
                "estimates:read", "estimates:write",
                "reports:read",
                "audit:read"  # Own actions only
            ],
            UserRole.VIEWER: [
                "estimates:read",
                "reports:read"
            ]
        }
        
        return permission in permission_matrix.get(self.role, [])
    
    def can_access_cost_details(self) -> bool:
        """Check if user can see detailed cost breakdowns."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_approve_estimates(self) -> bool:
        """Check if user can approve estimates."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_modify_costs(self) -> bool:
        """Check if user can modify cost data."""
        return self.role == UserRole.ADMIN
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role == UserRole.ADMIN
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dictionary representation of user
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if self.role else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "phone_number": self.phone_number,
            "department": self.department,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data["created_by"] = self.created_by
            data["updated_by"] = self.updated_by
            data["deleted_at"] = self.deleted_at.isoformat() if self.deleted_at else None
            data["deleted_by"] = self.deleted_by
        
        return data