#!/usr/bin/env python3
"""
Quick start script to get the Tree Service Estimating app running.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def main():
    """Run the quick start process."""
    print("=== Tree Service Estimating App - Quick Start ===\n")
    
    # Change to project root
    os.chdir(project_root)
    
    # Check if .env exists
    if not (project_root / ".env").exists():
        print("❌ .env file not found!")
        print("Please create a .env file first.")
        return 1
    
    # Install dependencies
    print("Step 1: Installing dependencies...")
    if sys.platform == "win32":
        pip_cmd = r"venv_linux\Scripts\pip.exe install -r requirements.txt"
    else:
        pip_cmd = "pip install -r requirements.txt"
    
    if not run_command(pip_cmd, "Installing Python packages"):
        print("\n💡 Try creating a fresh virtual environment:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   source venv/bin/activate  # Linux/Mac")
        return 1
    
    # Create uploads directory
    print("\nStep 2: Creating directories...")
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✅ Created uploads and logs directories")
    
    # Initialize database (SQLite for quick start)
    print("\nStep 3: Database setup...")
    print("⚠️  Note: Using SQLite for quick start. For production, use PostgreSQL.")
    
    # Update DATABASE_URL temporarily for SQLite
    import shutil
    shutil.copy(".env", ".env.backup")
    
    with open(".env", "r") as f:
        content = f.read()
    
    # Replace PostgreSQL URL with SQLite
    content = content.replace(
        "DATABASE_URL=postgresql://treeservice:password123@localhost:5432/treeservice_dev",
        "DATABASE_URL=sqlite:///./treeservice.db"
    )
    
    with open(".env", "w") as f:
        f.write(content)
    
    print("✅ Configured SQLite database for quick start")
    
    # Create initial migration if needed
    print("\nStep 4: Database migrations...")
    if not (project_root / "alembic" / "versions").exists():
        os.makedirs(project_root / "alembic" / "versions", exist_ok=True)
    
    # Check if any migrations exist
    versions_dir = project_root / "alembic" / "versions"
    if not any(versions_dir.glob("*.py")):
        print("Creating initial migration...")
        run_command(
            "alembic revision --autogenerate -m \"Initial migration\"",
            "Creating initial migration"
        )
    
    # Run migrations
    run_command("alembic upgrade head", "Applying database migrations")
    
    # Start the application
    print("\nStep 5: Starting the application...")
    print("\n" + "="*50)
    print("🚀 Starting Tree Service Estimating App...")
    print("="*50)
    print("\nThe app will be available at:")
    print("  - API: http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs")
    print("  - Health: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the app
    if sys.platform == "win32":
        uvicorn_cmd = r"venv_linux\Scripts\uvicorn.exe src.main:app --reload --port 8000"
    else:
        uvicorn_cmd = "uvicorn src.main:app --reload --port 8000"
    
    try:
        subprocess.run(uvicorn_cmd, shell=True)
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        
        # Restore original .env
        if (project_root / ".env.backup").exists():
            shutil.move(".env.backup", ".env")
            print("✅ Restored original .env file")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())