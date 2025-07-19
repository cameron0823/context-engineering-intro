-- Performance indexes for Cox Tree Service Estimating Application
-- Run this script to add indexes for improved query performance

-- Estimates table indexes
CREATE INDEX IF NOT EXISTS idx_estimates_created_at ON estimates(created_at);
CREATE INDEX IF NOT EXISTS idx_estimates_status ON estimates(status);
CREATE INDEX IF NOT EXISTS idx_estimates_customer_email ON estimates(customer_email);
CREATE INDEX IF NOT EXISTS idx_estimates_valid_until ON estimates(valid_until);
CREATE INDEX IF NOT EXISTS idx_estimates_deleted_at ON estimates(deleted_at);
CREATE INDEX IF NOT EXISTS idx_estimates_created_by ON estimates(created_by);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_estimates_status_created_at ON estimates(status, created_at);
CREATE INDEX IF NOT EXISTS idx_estimates_created_by_status ON estimates(created_by, status);

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_is_active_role ON users(is_active, role);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

-- Labor rates table indexes
CREATE INDEX IF NOT EXISTS idx_labor_rates_role_effective ON labor_rates(role, effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_labor_rates_is_active ON labor_rates(is_active);

-- Equipment costs table indexes
CREATE INDEX IF NOT EXISTS idx_equipment_costs_type_available ON equipment_costs(equipment_type, is_available);
CREATE INDEX IF NOT EXISTS idx_equipment_costs_effective ON equipment_costs(effective_from, effective_to);

-- Overhead settings table indexes
CREATE INDEX IF NOT EXISTS idx_overhead_settings_default ON overhead_settings(is_default);
CREATE INDEX IF NOT EXISTS idx_overhead_settings_effective ON overhead_settings(effective_from, effective_to);

-- Audit log table indexes (most critical for performance)
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_correlation_id ON audit_logs(correlation_id);

-- Composite index for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_action_created ON audit_logs(table_name, action, created_at);

-- Analyze tables to update statistics after adding indexes
ANALYZE estimates;
ANALYZE users;
ANALYZE labor_rates;
ANALYZE equipment_costs;
ANALYZE overhead_settings;
ANALYZE audit_logs;