"""
Script to create the first admin user for the Tree Service app.
Run this locally with your production database URL.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.user import User, UserRole
from src.core.security import get_password_hash
from src.db.base import Base
import os
from dotenv import load_dotenv

load_dotenv()

async def create_admin_user():
    # Use your production DATABASE_URL here
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    
    # Create engine
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create admin user
    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        existing = await session.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        )
        if existing.first():
            print("Admin user already exists!")
            return
            
        # Create new admin
        admin = User(
            username="admin",
            email="admin@coxtreeservice.com",
            full_name="Administrator",
            hashed_password=get_password_hash("ChangeMe123!"),  # CHANGE THIS PASSWORD!
            role=UserRole.ADMIN,
            is_active=True
        )
        
        session.add(admin)
        await session.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: ChangeMe123!")
        print("IMPORTANT: Change this password after first login!")

if __name__ == "__main__":
    asyncio.run(create_admin_user())