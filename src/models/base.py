"""
Base model with audit trail functionality.
All other models should inherit from this base model.
"""
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import Column, Integer, DateTime, String, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.db.session import Base


class BaseModel(Base):
    """
    Base model class with audit fields and soft delete functionality.
    All models should inherit from this class.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Audit fields
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False
    )
    created_by = Column(String, nullable=False)  # User ID who created the record
    updated_by = Column(String, nullable=True)   # User ID who last updated the record
    
    # Soft delete fields
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String, nullable=True)   # User ID who deleted the record
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        name = cls.__name__
        return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_') + 's'
    
    def soft_delete(self, user_id: str) -> None:
        """
        Soft delete the record.
        
        Args:
            user_id: ID of the user performing the deletion
        """
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
    
    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None
        self.deleted_by = None
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: dict, user_id: str) -> None:
        """
        Update model from dictionary.
        
        Args:
            data: Dictionary with field values
            user_id: ID of the user performing the update
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'created_by']:
                setattr(self, key, value)
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """
    Mixin for timestamp fields without user tracking.
    Useful for system-generated records.
    """
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False
    )


class AuditMixin(TimestampMixin):
    """
    Mixin for full audit trail including user tracking.
    """
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String, nullable=True)
    
    def soft_delete(self, user_id: str) -> None:
        """Soft delete the record."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
    
    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None
        self.deleted_by = None
    
    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None


# Event listeners for automatic audit trail
def set_created_by(mapper, connection, target):
    """Set created_by field on insert."""
    # This will be overridden in the API layer with actual user ID
    if not target.created_by:
        target.created_by = "system"


def set_updated_by(mapper, connection, target):
    """Set updated_by field on update."""
    # This will be overridden in the API layer with actual user ID
    if hasattr(target, 'updated_by') and not target.updated_by:
        target.updated_by = "system"


# Register event listeners for all models inheriting from BaseModel
event.listen(BaseModel, 'before_insert', set_created_by, propagate=True)
event.listen(BaseModel, 'before_update', set_updated_by, propagate=True)