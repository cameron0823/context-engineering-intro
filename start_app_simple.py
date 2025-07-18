#!/usr/bin/env python3
"""
Simple startup script for Tree Service Estimating App
Works around dependency issues by using minimal requirements
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=== Tree Service Estimating App - Simple Start ===\n")
    
    # Essential packages only
    essential_packages = [
        "fastapi",
        "uvicorn",
        "python-multipart", 
        "sqlalchemy",
        "pydantic",
        "pydantic-settings",
        "python-dotenv",
        "httpx",
        "aiosqlite",  # For SQLite support
    ]
    
    print("Installing essential packages...")
    for package in essential_packages:
        print(f"Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], 
                      capture_output=True)
    
    print("\n✅ Essential packages installed!")
    
    # Update .env to use SQLite
    print("\nConfiguring SQLite database...")
    if Path(".env").exists():
        with open(".env", "r") as f:
            content = f.read()
        
        # Backup
        with open(".env.backup", "w") as f:
            f.write(content)
        
        # Replace PostgreSQL with SQLite
        content = content.replace(
            "DATABASE_URL=postgresql://treeservice:password123@localhost:5432/treeservice_dev",
            "DATABASE_URL=sqlite:///./treeservice.db"
        )
        
        with open(".env", "w") as f:
            f.write(content)
        
        print("✅ Database configured for SQLite")
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✅ Directories created")
    
    # Create a minimal init script for database
    init_script = '''
from sqlalchemy import create_engine
from src.models.base import Base
from src.models.user import User
from src.models.costs import LaborRate, EquipmentCost
from src.models.estimate import Estimate
from src.models.audit import AuditLog

engine = create_engine("sqlite:///./treeservice.db")
Base.metadata.create_all(engine)
print("✅ Database tables created!")
'''
    
    with open("init_db_simple.py", "w") as f:
        f.write(init_script)
    
    print("\nInitializing database...")
    subprocess.run([sys.executable, "init_db_simple.py"])
    
    print("\n" + "="*50)
    print("🚀 Starting Tree Service Estimating App...")
    print("="*50)
    print("\nThe app will be available at:")
    print("  - API: http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs") 
    print("  - Health: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Import and run uvicorn directly
    import uvicorn
    
    try:
        uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    finally:
        # Restore .env
        if Path(".env.backup").exists():
            import shutil
            shutil.move(".env.backup", ".env")
            print("✅ Original .env restored")

if __name__ == "__main__":
    main()