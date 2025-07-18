"""
Create test users for the Tree Service Estimating application.
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import async_session_maker
from src.models.user import User
from src.core.security import pwd_context
from src.models.costs import LaborRate, EquipmentCost, VehicleRate


async def create_test_users():
    """Create test users with different roles."""
    async with async_session_maker() as db:
        try:
            # Check if users already exist
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.email == "admin@treeservice.com"))
            existing_admin = result.scalars().first()
            
            if existing_admin:
                print("Test users already exist!")
                return
            
            # Create test users
            users = [
                {
                    "email": "admin@treeservice.com",
                    "username": "admin",
                    "full_name": "Admin User",
                    "role": "ADMIN",
                    "password": "admin123"
                },
                {
                    "email": "manager@treeservice.com",
                    "username": "manager",
                    "full_name": "Manager User",
                    "role": "MANAGER",
                    "password": "manager123"
                },
                {
                    "email": "estimator@treeservice.com",
                    "username": "estimator",
                    "full_name": "Estimator User",
                    "role": "ESTIMATOR",
                    "password": "estimator123"
                },
                {
                    "email": "viewer@treeservice.com",
                    "username": "viewer",
                    "full_name": "Viewer User",
                    "role": "VIEWER",
                    "password": "viewer123"
                }
            ]
            
            for user_data in users:
                password = user_data.pop("password")
                user = User(**user_data, hashed_password=pwd_context.hash(password))
                db.add(user)
                print(f"Created user: {user.username} ({user.role})")
            
            # Create initial costs data
            from datetime import date
            
            labor_rate = LaborRate(
                role="Crew Member",
                hourly_rate=45.00,
                effective_from=date.today()
            )
            db.add(labor_rate)
            print("Created labor rate: Crew Member - $45.00/hour")
            
            equipment_cost = EquipmentCost(
                equipment_name="Chainsaw",
                equipment_type="saw",
                hourly_rate=25.00
            )
            db.add(equipment_cost)
            print("Created equipment cost: Chainsaw - $25.00/hour")
            
            vehicle_rate = VehicleRate(
                vehicle_type="truck",
                per_mile_rate=0.50,
                effective_from=date.today()
            )
            db.add(vehicle_rate)
            print("Created vehicle rate: Truck - $0.50/mile")
            
            await db.commit()
            print("\nAll test data created successfully!")
            
        except Exception as e:
            print(f"Error creating test users: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_test_users())