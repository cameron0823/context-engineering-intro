#!/usr/bin/env python3
"""
Verify that the environment is properly configured for the Tree Service Estimating app.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = project_root / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   Please create a .env file based on .env.example")
        return False
    
    print("✅ .env file found")
    
    # Check required variables
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "GOOGLE_MAPS_API_KEY",
        "QUICKBOOKS_CLIENT_ID",
        "QUICKBOOKS_CLIENT_SECRET",
        "FUEL_API_KEY"
    ]
    
    with open(env_path) as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are present")
    return True


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\nChecking Python dependencies...")
    
    try:
        import fastapi
        print("✅ FastAPI installed")
    except ImportError:
        print("❌ FastAPI not installed")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy installed")
    except ImportError:
        print("❌ SQLAlchemy not installed")
        return False
    
    try:
        import httpx
        print("✅ HTTPX installed")
    except ImportError:
        print("❌ HTTPX not installed")
        return False
    
    try:
        import redis
        print("✅ Redis-py installed")
    except ImportError:
        print("❌ Redis-py not installed")
        return False
    
    return True


def check_external_apis():
    """Test external API configurations."""
    print("\nChecking external API configurations...")
    
    try:
        from src.core.config import settings
        
        # Check Google Maps
        if settings.GOOGLE_MAPS_API_KEY and len(settings.GOOGLE_MAPS_API_KEY) > 10:
            print("✅ Google Maps API key configured")
        else:
            print("⚠️  Google Maps API key may be invalid")
        
        # Check QuickBooks
        if settings.QUICKBOOKS_CLIENT_ID and len(settings.QUICKBOOKS_CLIENT_ID) > 10:
            print("✅ QuickBooks credentials configured")
        else:
            print("⚠️  QuickBooks credentials may be invalid")
        
        # Check Fuel API
        if settings.FUEL_API_KEY and len(settings.FUEL_API_KEY) > 10:
            print("✅ Fuel API key configured")
        else:
            print("⚠️  Fuel API key may be invalid")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


def check_database_url():
    """Check if database URL is properly formatted."""
    print("\nChecking database configuration...")
    
    try:
        from src.core.config import settings
        
        if settings.DATABASE_URL.startswith("postgresql://"):
            print("✅ PostgreSQL database URL configured")
        elif settings.DATABASE_URL.startswith("sqlite://"):
            print("⚠️  Using SQLite database (not recommended for production)")
        else:
            print("❌ Invalid database URL format")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database URL: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=== Tree Service Estimating App - Setup Verification ===\n")
    
    all_good = True
    
    # Check .env file
    if not check_env_file():
        all_good = False
    
    # Check dependencies
    if not check_dependencies():
        all_good = False
        print("\n💡 Run: pip install -r requirements.txt")
    
    # Check database
    if not check_database_url():
        all_good = False
    
    # Check external APIs
    if not check_external_apis():
        all_good = False
    
    print("\n" + "="*50)
    
    if all_good:
        print("✅ Setup verification complete! Your environment is ready.")
        print("\nNext steps:")
        print("1. Start Docker services: docker-compose up -d")
        print("2. Run migrations: alembic upgrade head")
        print("3. Start the app: uvicorn src.main:app --reload")
    else:
        print("❌ Some issues were found. Please fix them before running the app.")
        print("\n⚠️  WARNING: The API keys in your .env file should be kept secret!")
        print("   Never commit them to version control.")
    
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())