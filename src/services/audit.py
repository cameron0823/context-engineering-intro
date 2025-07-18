"""
Audit service for tracking changes to entities.
"""
from typing import Optional, List, Dict, Any, Type
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
import json

from src.models.audit import AuditLog
from src.models.base import BaseModel


class AuditService:
    """Service for managing audit logs."""
    
    @staticmethod
    async def log_change(
        db: AsyncSession,
        entity: BaseModel,
        action: str,
        user_id: str,
        old_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log a change to an entity.
        
        Args:
            db: Database session
            entity: The entity being changed
            action: Type of action (INSERT, UPDATE, DELETE, RESTORE)
            user_id: ID of the user making the change
            old_values: Previous state (for UPDATE, DELETE)
            ip_address: User's IP address
            user_agent: User's browser/client info
            context: Additional context
            correlation_id: ID for tracking related changes
            
        Returns:
            Created audit log entry
        """
        # Get current values
        new_values = entity.to_dict() if hasattr(entity, 'to_dict') else None
        
        # Calculate changed fields for UPDATE
        changed_fields = None
        if action == "UPDATE" and old_values and new_values:
            changed_fields = [
                key for key in new_values 
                if key in old_values and old_values[key] != new_values[key]
            ]
        
        # Create audit log
        audit_log = AuditLog.create_audit_log(
            table_name=entity.__tablename__,
            record_id=entity.id,
            action=action,
            changed_by=user_id,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            ip_address=ip_address,
            user_agent=user_agent,
            context=context,
            correlation_id=correlation_id
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    async def get_entity_history(
        db: AsyncSession,
        table_name: str,
        record_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit history for a specific entity.
        
        Args:
            db: Database session
            table_name: Name of the table
            record_id: ID of the record
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of audit logs for the entity
        """
        query = select(AuditLog).where(
            and_(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id
            )
        ).order_by(AuditLog.changed_at.desc())
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_activity(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user
            start_date: Start date filter
            end_date: End date filter
            action: Action type filter
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of audit logs for the user
        """
        conditions = [AuditLog.changed_by == user_id]
        
        if start_date:
            conditions.append(AuditLog.changed_at >= start_date)
        if end_date:
            conditions.append(AuditLog.changed_at <= end_date)
        if action:
            conditions.append(AuditLog.action == action)
        
        query = select(AuditLog).where(
            and_(*conditions)
        ).order_by(AuditLog.changed_at.desc())
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_changes_by_correlation(
        db: AsyncSession,
        correlation_id: str
    ) -> List[AuditLog]:
        """
        Get all changes with the same correlation ID.
        
        Args:
            db: Database session
            correlation_id: Correlation ID to search for
            
        Returns:
            List of related audit logs
        """
        query = select(AuditLog).where(
            AuditLog.correlation_id == correlation_id
        ).order_by(AuditLog.changed_at)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def reconstruct_state_at_time(
        db: AsyncSession,
        table_name: str,
        record_id: int,
        target_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Reconstruct the state of an entity at a specific time.
        
        Args:
            db: Database session
            table_name: Name of the table
            record_id: ID of the record
            target_time: Point in time to reconstruct
            
        Returns:
            Dictionary representing the entity state at that time
        """
        # Get all changes up to target time
        query = select(AuditLog).where(
            and_(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id,
                AuditLog.changed_at <= target_time
            )
        ).order_by(AuditLog.changed_at)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        if not logs:
            return None
        
        # Start with the first INSERT
        state = None
        for log in logs:
            if log.action == "INSERT":
                state = log.new_values.copy() if log.new_values else {}
            elif log.action == "UPDATE" and state and log.new_values:
                # Apply updates
                state.update(log.new_values)
            elif log.action == "DELETE":
                # Record was deleted at this point
                return None
            elif log.action == "RESTORE" and log.new_values:
                # Record was restored
                state = log.new_values.copy()
        
        return state
    
    @staticmethod
    async def get_audit_summary(
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get summary statistics for audit logs.
        
        Args:
            db: Database session
            start_date: Start date for summary
            end_date: End date for summary
            
        Returns:
            Dictionary with summary statistics
        """
        # Count by action
        action_counts = await db.execute(
            select(
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            ).where(
                and_(
                    AuditLog.changed_at >= start_date,
                    AuditLog.changed_at <= end_date
                )
            ).group_by(AuditLog.action)
        )
        
        # Count by table
        table_counts = await db.execute(
            select(
                AuditLog.table_name,
                func.count(AuditLog.id).label('count')
            ).where(
                and_(
                    AuditLog.changed_at >= start_date,
                    AuditLog.changed_at <= end_date
                )
            ).group_by(AuditLog.table_name)
        )
        
        # Most active users
        user_counts = await db.execute(
            select(
                AuditLog.changed_by,
                func.count(AuditLog.id).label('count')
            ).where(
                and_(
                    AuditLog.changed_at >= start_date,
                    AuditLog.changed_at <= end_date
                )
            ).group_by(AuditLog.changed_by)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "by_action": {row[0]: row[1] for row in action_counts},
            "by_table": {row[0]: row[1] for row in table_counts},
            "top_users": [{"user_id": row[0], "count": row[1]} for row in user_counts]
        }
    
    @staticmethod
    async def cleanup_old_logs(
        db: AsyncSession,
        retention_days: int = 2555  # 7 years default
    ) -> int:
        """
        Clean up audit logs older than retention period.
        
        Args:
            db: Database session
            retention_days: Number of days to retain logs
            
        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete old logs
        result = await db.execute(
            select(AuditLog).where(
                AuditLog.changed_at < cutoff_date
            )
        )
        old_logs = result.scalars().all()
        
        for log in old_logs:
            await db.delete(log)
        
        await db.commit()
        return len(old_logs)


# Create a singleton instance
audit_service = AuditService()