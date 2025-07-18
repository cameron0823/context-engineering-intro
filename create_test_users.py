#!/usr/bin/env python3
"""
Create test users with proper password hashing
"""
import os
import asyncio
from datetime import datetime

# Set environment for SQLite
os.environ["DATABASE_URL"] = "sqlite:///./treeservice_dev.db"
os.environ["SECRET_KEY"] = "dev-secret-key"

from src.db.session import async_session_maker
from src.models.user import User, UserRole
from src.core.security import security
from sqlalchemy import select


async def create_or_update_user(session, username, email, password, role, full_name):
    """Create or update a test user"""
    # Check if user exists
    result = await session.execute(
        select(User).where(User.username == username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Update existing user
        existing_user.hashed_password = security.get_password_hash(password)
        existing_user.role = role
        existing_user.is_active = True
        existing_user.is_verified = True
        existing_user.email = email
        existing_user.full_name = full_name
        print(f"✅ Updated existing user: {username}")
    else:
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=security.get_password_hash(password),
            role=role,
            is_active=True,
            is_verified=True,
            created_by="system"
        )
        session.add(user)
        print(f"✅ Created new user: {username}")


async def main():
    """Create all test users"""
    print("Creating test users with proper password hashing...")
    print("=" * 60)
    
    users = [
        {
            "username": "admin",
            "email": "admin@treeservice.com",
            "password": "Admin123!",
            "role": UserRole.ADMIN,
            "full_name": "Admin User"
        },
        {
            "username": "manager",
            "email": "manager@treeservice.com",
            "password": "Manager123!",
            "role": UserRole.MANAGER,
            "full_name": "Manager User"
        },
        {
            "username": "estimator",
            "email": "estimator@treeservice.com",
            "password": "Estimator123!",
            "role": UserRole.ESTIMATOR,
            "full_name": "Estimator User"
        },
        {
            "username": "viewer",
            "email": "viewer@treeservice.com",
            "password": "Viewer123!",
            "role": UserRole.VIEWER,
            "full_name": "Viewer User"
        }
    ]
    
    try:
        async with async_session_maker() as session:
            for user_data in users:
                await create_or_update_user(
                    session,
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                    role=user_data["role"],
                    full_name=user_data["full_name"]
                )
            
            await session.commit()
            
        print("\n✅ All test users created/updated successfully!")
        print("\nTest Accounts:")
        print("-" * 40)
        for user in users:
            print(f"{user['role'].value.title():12} {user['username']:10} / {user['password']}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())