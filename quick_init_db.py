#!/usr/bin/env python3
"""
Quick database initialization without relationships
"""
import sqlite3
import hashlib
from datetime import datetime
from decimal import Decimal

# Create SQLite database
conn = sqlite3.connect('treeservice_dev.db')
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    role VARCHAR(20) DEFAULT 'viewer',
    phone_number VARCHAR(20),
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255)
)
''')

# Create labor_rates table
cursor.execute('''
CREATE TABLE IF NOT EXISTS labor_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role VARCHAR(100) NOT NULL,
    hourly_rate DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    effective_date DATE NOT NULL,
    effective_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL
)
''')

# Create equipment_costs table
cursor.execute('''
CREATE TABLE IF NOT EXISTS equipment_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    equipment_id VARCHAR(50) UNIQUE NOT NULL,
    hourly_cost DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    is_available BOOLEAN DEFAULT 1,
    effective_date DATE NOT NULL,
    effective_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL
)
''')

# Create overhead_settings table
cursor.execute('''
CREATE TABLE IF NOT EXISTS overhead_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    overhead_percent DECIMAL(5,2) NOT NULL,
    profit_percent DECIMAL(5,2) NOT NULL,
    safety_buffer_percent DECIMAL(5,2) NOT NULL,
    vehicle_rate_per_mile DECIMAL(10,2) NOT NULL,
    driver_hourly_rate DECIMAL(10,2) NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL
)
''')

print("✅ Tables created")

# Insert test users

import bcrypt

def simple_hash(password):
    # Use bcrypt for secure password hashing
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

users = [
    ('admin', 'admin@treeservice.com', 'Admin User', simple_hash('Admin123!'), 1, 1, 'admin'),
    ('manager', 'manager@treeservice.com', 'Manager User', simple_hash('Manager123!'), 1, 1, 'manager'),
    ('estimator', 'estimator@treeservice.com', 'Estimator User', simple_hash('Estimator123!'), 1, 1, 'estimator'),
    ('viewer', 'viewer@treeservice.com', 'Viewer User', simple_hash('Viewer123!'), 1, 1, 'viewer')
]

for user in users:
    cursor.execute('''
        INSERT INTO users (username, email, full_name, hashed_password, is_active, is_verified, role, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'system')
    ''', user)

print("✅ Test users created")

# Insert labor rates
labor_rates = [
    ('Lead Arborist', 55.00, 'skilled', datetime.now().date()),
    ('Certified Arborist', 50.00, 'skilled', datetime.now().date()),
    ('Climber', 45.00, 'skilled', datetime.now().date()),
    ('Equipment Operator', 40.00, 'skilled', datetime.now().date()),
    ('Ground Worker', 25.00, 'general', datetime.now().date()),
    ('Trainee', 20.00, 'general', datetime.now().date())
]

for rate in labor_rates:
    cursor.execute('''
        INSERT INTO labor_rates (role, hourly_rate, category, effective_date, created_by)
        VALUES (?, ?, ?, ?, 'system')
    ''', rate)

print("✅ Labor rates created")

# Insert equipment costs
equipment = [
    ('Wood Chipper (12")', 'chipper', 75.00, 'processing', datetime.now().date()),
    ('Bucket Truck (60ft)', 'bucket_truck', 125.00, 'aerial', datetime.now().date()),
    ('Crane (30 ton)', 'crane', 350.00, 'heavy', datetime.now().date()),
    ('Stump Grinder', 'stump_grinder', 85.00, 'processing', datetime.now().date()),
    ('Dump Truck', 'dump_truck', 65.00, 'transport', datetime.now().date()),
    ('Chainsaw', 'chainsaw', 15.00, 'tools', datetime.now().date())
]

for eq in equipment:
    cursor.execute('''
        INSERT INTO equipment_costs (name, equipment_id, hourly_cost, category, effective_date, created_by)
        VALUES (?, ?, ?, ?, ?, 'system')
    ''', eq)

print("✅ Equipment costs created")

# Insert overhead settings
cursor.execute('''
    INSERT INTO overhead_settings 
    (overhead_percent, profit_percent, safety_buffer_percent, vehicle_rate_per_mile, driver_hourly_rate, effective_date, created_by)
    VALUES (25.0, 35.0, 10.0, 0.65, 25.00, ?, 'system')
''', (datetime.now().date(),))

print("✅ Overhead settings created")

# Commit and close
conn.commit()
conn.close()

print("\n✅ Database initialization complete!")
print("\nTest Users:")
print("  Admin:     admin / Admin123!")
print("  Manager:   manager / Manager123!")
print("  Estimator: estimator / Estimator123!")
print("  Viewer:    viewer / Viewer123!")