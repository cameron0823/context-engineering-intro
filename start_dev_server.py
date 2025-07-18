#!/usr/bin/env python3
"""
Development server starter with SQLite database
For quick testing without PostgreSQL
"""
import os
import sys
import subprocess
from pathlib import Path

# Set up environment for SQLite development
os.environ["DATABASE_URL"] = "sqlite:///./treeservice_dev.db"
os.environ["SECRET_KEY"] = "dev-secret-key-change-in-production"
os.environ["DEBUG"] = "True"
os.environ["ENVIRONMENT"] = "development"

# Mock API keys for development
os.environ["GOOGLE_MAPS_API_KEY"] = "TEST_GOOGLE_MAPS_API_KEY"
os.environ["QUICKBOOKS_CLIENT_ID"] = "TEST_QUICKBOOKS_CLIENT_ID"
os.environ["QUICKBOOKS_CLIENT_SECRET"] = "TEST_QUICKBOOKS_CLIENT_SECRET"
os.environ["QUICKBOOKS_COMPANY_ID"] = "TEST_QUICKBOOKS_COMPANY_ID"
os.environ["FUEL_API_KEY"] = "TEST_FUEL_API_KEY"

# Redis URL (optional for development)
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

print("Starting Tree Service Estimating App in Development Mode...")
print("=" * 60)
print("Using SQLite database: treeservice_dev.db")
print("Access the app at: http://localhost:8002")
print("API Documentation: http://localhost:8002/docs")
print("=" * 60)

# Start the server
subprocess.run([
    sys.executable, "-m", "uvicorn", 
    "src.main:app", 
    "--reload", 
    "--port", "8002",
    "--host", "0.0.0.0"
])