"""
Audit log model for tracking all changes to entities.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from src.db.session import Base


class AuditLog(Base):
    """
    Audit log for tracking all changes to entities.
    Stores before/after values and changed fields.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )
    
    # Entity information
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    
    # Action type
    action = Column(
        String(20), 
        nullable=False,
        index=True
    )  # INSERT, UPDATE, DELETE, RESTORE
    
    # User who made the change
    changed_by = Column(String, nullable=False, index=True)
    changed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # IP address and user agent for additional tracking
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    
    # Change details
    old_values = Column(JSON, nullable=True)  # State before change
    new_values = Column(JSON, nullable=True)  # State after change
    changed_fields = Column(JSON, nullable=True)  # Only the fields that changed
    
    # Additional context
    context = Column(JSON, nullable=True)  # Any additional context (e.g., reason for change)
    correlation_id = Column(String, nullable=True, index=True)  # For tracking related changes
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_entity', 'table_name', 'record_id'),
        Index('idx_audit_user_time', 'changed_by', 'changed_at'),
        Index('idx_audit_action_time', 'action', 'changed_at'),
        Index('idx_audit_correlation', 'correlation_id'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, table={self.table_name}, "
            f"record={self.record_id}, action={self.action})>"
        )
    
    @classmethod
    def create_audit_log(
        cls,
        table_name: str,
        record_id: int,
        action: str,
        changed_by: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        changed_fields: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> "AuditLog":
        """
        Create a new audit log entry.
        
        Args:
            table_name: Name of the table being audited
            record_id: ID of the record being changed
            action: Type of action (INSERT, UPDATE, DELETE, RESTORE)
            changed_by: User ID who made the change
            old_values: State before change (for UPDATE, DELETE)
            new_values: State after change (for INSERT, UPDATE)
            changed_fields: Only the fields that changed (for UPDATE)
            ip_address: IP address of the user
            user_agent: User agent string
            context: Additional context
            correlation_id: ID for tracking related changes
        
        Returns:
            New AuditLog instance
        """
        return cls(
            table_name=table_name,
            record_id=record_id,
            action=action,
            changed_by=changed_by,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            ip_address=ip_address,
            user_agent=user_agent,
            context=context,
            correlation_id=correlation_id
        )
    
    def get_field_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a dictionary of field changes.
        
        Returns:
            Dictionary with field names as keys and {old, new} as values
        """
        if not self.changed_fields:
            return {}
        
        changes = {}
        for field in self.changed_fields:
            changes[field] = {
                "old": self.old_values.get(field) if self.old_values else None,
                "new": self.new_values.get(field) if self.new_values else None
            }
        return changes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "audit_id": str(self.audit_id),
            "table_name": self.table_name,
            "record_id": self.record_id,
            "action": self.action,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "changed_fields": self.changed_fields,
            "context": self.context,
            "correlation_id": self.correlation_id
        }


class AuditLogView(Base):
    """
    Materialized view for efficient audit log queries.
    This is created via migration for performance.
    """
    __tablename__ = "audit_log_summary_view"
    __table_args__ = {"info": {"is_view": True}}
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String)
    record_id = Column(Integer)
    action = Column(String)
    changed_by = Column(String)
    changed_at = Column(DateTime)
    field_count = Column(Integer)  # Number of fields changed
    
    # This view would be created in a migration with:
    # CREATE MATERIALIZED VIEW audit_log_summary_view AS
    # SELECT 
    #     id,
    #     table_name,
    #     record_id,
    #     action,
    #     changed_by,
    #     changed_at,
    #     jsonb_array_length(changed_fields) as field_count
    # FROM audit_logs;