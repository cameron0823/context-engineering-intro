"""Add performance indexes

Revision ID: 001
Revises: 
Create Date: 2024-07-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for commonly queried fields."""
    
    # Estimates table indexes
    op.create_index('idx_estimates_created_at', 'estimates', ['created_at'])
    op.create_index('idx_estimates_status', 'estimates', ['status'])
    op.create_index('idx_estimates_customer_email', 'estimates', ['customer_email'])
    op.create_index('idx_estimates_valid_until', 'estimates', ['valid_until'])
    op.create_index('idx_estimates_deleted_at', 'estimates', ['deleted_at'])
    op.create_index('idx_estimates_created_by', 'estimates', ['created_by'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_estimates_status_created_at', 'estimates', ['status', 'created_at'])
    op.create_index('idx_estimates_created_by_status', 'estimates', ['created_by', 'status'])
    
    # Users table indexes
    op.create_index('idx_users_is_active_role', 'users', ['is_active', 'role'])
    op.create_index('idx_users_department', 'users', ['department'])
    op.create_index('idx_users_deleted_at', 'users', ['deleted_at'])
    
    # Labor rates table indexes
    op.create_index('idx_labor_rates_role_effective', 'labor_rates', ['role', 'effective_from', 'effective_to'])
    op.create_index('idx_labor_rates_is_active', 'labor_rates', ['is_active'])
    
    # Equipment costs table indexes
    op.create_index('idx_equipment_costs_type_available', 'equipment_costs', ['equipment_type', 'is_available'])
    op.create_index('idx_equipment_costs_effective', 'equipment_costs', ['effective_from', 'effective_to'])
    
    # Overhead settings table indexes
    op.create_index('idx_overhead_settings_default', 'overhead_settings', ['is_default'])
    op.create_index('idx_overhead_settings_effective', 'overhead_settings', ['effective_from', 'effective_to'])
    
    # Audit log table indexes
    op.create_index('idx_audit_logs_table_record', 'audit_logs', ['table_name', 'record_id'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_correlation_id', 'audit_logs', ['correlation_id'])
    
    # Composite index for audit log queries
    op.create_index('idx_audit_logs_table_action_created', 'audit_logs', ['table_name', 'action', 'created_at'])


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop audit log indexes
    op.drop_index('idx_audit_logs_table_action_created', 'audit_logs')
    op.drop_index('idx_audit_logs_correlation_id', 'audit_logs')
    op.drop_index('idx_audit_logs_created_at', 'audit_logs')
    op.drop_index('idx_audit_logs_action', 'audit_logs')
    op.drop_index('idx_audit_logs_user_id', 'audit_logs')
    op.drop_index('idx_audit_logs_table_record', 'audit_logs')
    
    # Drop overhead settings indexes
    op.drop_index('idx_overhead_settings_effective', 'overhead_settings')
    op.drop_index('idx_overhead_settings_default', 'overhead_settings')
    
    # Drop equipment costs indexes
    op.drop_index('idx_equipment_costs_effective', 'equipment_costs')
    op.drop_index('idx_equipment_costs_type_available', 'equipment_costs')
    
    # Drop labor rates indexes
    op.drop_index('idx_labor_rates_is_active', 'labor_rates')
    op.drop_index('idx_labor_rates_role_effective', 'labor_rates')
    
    # Drop users indexes
    op.drop_index('idx_users_deleted_at', 'users')
    op.drop_index('idx_users_department', 'users')
    op.drop_index('idx_users_is_active_role', 'users')
    
    # Drop estimates indexes
    op.drop_index('idx_estimates_created_by_status', 'estimates')
    op.drop_index('idx_estimates_status_created_at', 'estimates')
    op.drop_index('idx_estimates_created_by', 'estimates')
    op.drop_index('idx_estimates_deleted_at', 'estimates')
    op.drop_index('idx_estimates_valid_until', 'estimates')
    op.drop_index('idx_estimates_customer_email', 'estimates')
    op.drop_index('idx_estimates_status', 'estimates')
    op.drop_index('idx_estimates_created_at', 'estimates')