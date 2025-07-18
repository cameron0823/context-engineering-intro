-- PostgreSQL initialization script

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'estimator', 'viewer');
CREATE TYPE estimate_status AS ENUM ('draft', 'pending', 'approved', 'rejected', 'invoiced');

-- Create audit trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create function to log changes to audit table
CREATE OR REPLACE FUNCTION log_audit_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_data jsonb;
    new_data jsonb;
    changed_fields jsonb;
BEGIN
    IF TG_OP = 'INSERT' THEN
        new_data = to_jsonb(NEW);
        INSERT INTO audit_logs (
            table_name,
            record_id,
            action,
            changed_by,
            changed_at,
            new_values
        ) VALUES (
            TG_TABLE_NAME,
            NEW.id,
            TG_OP,
            NEW.created_by,
            CURRENT_TIMESTAMP,
            new_data
        );
    ELSIF TG_OP = 'UPDATE' THEN
        old_data = to_jsonb(OLD);
        new_data = to_jsonb(NEW);
        
        -- Calculate changed fields
        SELECT jsonb_object_agg(key, value)
        INTO changed_fields
        FROM jsonb_each(new_data)
        WHERE value != old_data->key;
        
        IF changed_fields IS NOT NULL AND changed_fields != '{}'::jsonb THEN
            INSERT INTO audit_logs (
                table_name,
                record_id,
                action,
                changed_by,
                changed_at,
                old_values,
                new_values,
                changed_fields
            ) VALUES (
                TG_TABLE_NAME,
                NEW.id,
                TG_OP,
                NEW.updated_by,
                CURRENT_TIMESTAMP,
                old_data,
                new_data,
                changed_fields
            );
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        old_data = to_jsonb(OLD);
        INSERT INTO audit_logs (
            table_name,
            record_id,
            action,
            changed_by,
            changed_at,
            old_values
        ) VALUES (
            TG_TABLE_NAME,
            OLD.id,
            TG_OP,
            OLD.deleted_by,
            CURRENT_TIMESTAMP,
            old_data
        );
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE treeservice_db TO treeservice;