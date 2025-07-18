#!/usr/bin/env python3
"""
Initialize development database with tables and test data
"""
import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Set SQLite for development
os.environ["DATABASE_URL"] = "sqlite:///./treeservice_dev.db"
os.environ["SECRET_KEY"] = "dev-secret-key"

from src.db.session import engine, Base, async_session_maker
from src.models.user import User, UserRole
from src.models.costs import LaborRate, EquipmentCost, OverheadSettings
from src.core.security import security


async def create_tables():
    """Create all database tables"""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from src.models import base, user, estimate, costs, audit
        
        # Drop all tables first for clean start
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created")


async def create_test_users():
    """Create test users for each role"""
    users = [
        {
            "username": "admin",
            "email": "admin@treeservice.com",
            "full_name": "Admin User",
            "password": "Admin123!",
            "role": UserRole.ADMIN,
            "is_verified": True
        },
        {
            "username": "manager",
            "email": "manager@treeservice.com",
            "full_name": "Manager User",
            "password": "Manager123!",
            "role": UserRole.MANAGER,
            "is_verified": True
        },
        {
            "username": "estimator",
            "email": "estimator@treeservice.com",
            "full_name": "Estimator User",
            "password": "Estimator123!",
            "role": UserRole.ESTIMATOR,
            "is_verified": True
        },
        {
            "username": "viewer",
            "email": "viewer@treeservice.com",
            "full_name": "Viewer User",
            "password": "Viewer123!",
            "role": UserRole.VIEWER,
            "is_verified": True
        }
    ]
    
    async with async_session_maker() as session:
        for user_data in users:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=security.get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_active=True,
                is_verified=user_data["is_verified"],
                created_by="system"
            )
            session.add(user)
        
        await session.commit()
        print("✅ Test users created")


async def create_labor_rates():
    """Create default labor rates"""
    rates = [
        {"role": "Lead Arborist", "hourly_rate": Decimal("55.00"), "category": "skilled"},
        {"role": "Certified Arborist", "hourly_rate": Decimal("50.00"), "category": "skilled"},
        {"role": "Climber", "hourly_rate": Decimal("45.00"), "category": "skilled"},
        {"role": "Equipment Operator", "hourly_rate": Decimal("40.00"), "category": "skilled"},
        {"role": "Ground Worker", "hourly_rate": Decimal("25.00"), "category": "general"},
        {"role": "Trainee", "hourly_rate": Decimal("20.00"), "category": "general"}
    ]
    
    async with async_session_maker() as session:
        for rate_data in rates:
            rate = LaborRate(
                role=rate_data["role"],
                hourly_rate=rate_data["hourly_rate"],
                category=rate_data["category"],
                effective_date=datetime.utcnow().date(),
                created_by="system"
            )
            session.add(rate)
        
        await session.commit()
        print("✅ Labor rates created")


async def create_equipment_costs():
    """Create default equipment costs"""
    equipment = [
        {
            "name": "Wood Chipper (12\")",
            "equipment_id": "chipper",
            "hourly_cost": Decimal("75.00"),
            "category": "processing"
        },
        {
            "name": "Bucket Truck (60ft)",
            "equipment_id": "bucket_truck",
            "hourly_cost": Decimal("125.00"),
            "category": "aerial"
        },
        {
            "name": "Crane (30 ton)",
            "equipment_id": "crane",
            "hourly_cost": Decimal("350.00"),
            "category": "heavy"
        },
        {
            "name": "Stump Grinder",
            "equipment_id": "stump_grinder",
            "hourly_cost": Decimal("85.00"),
            "category": "processing"
        },
        {
            "name": "Dump Truck",
            "equipment_id": "dump_truck",
            "hourly_cost": Decimal("65.00"),
            "category": "transport"
        },
        {
            "name": "Chainsaw",
            "equipment_id": "chainsaw",
            "hourly_cost": Decimal("15.00"),
            "category": "tools"
        }
    ]
    
    async with async_session_maker() as session:
        for eq_data in equipment:
            eq = EquipmentCost(
                name=eq_data["name"],
                equipment_id=eq_data["equipment_id"],
                hourly_cost=eq_data["hourly_cost"],
                category=eq_data["category"],
                is_available=True,
                effective_date=datetime.utcnow().date(),
                created_by="system"
            )
            session.add(eq)
        
        await session.commit()
        print("✅ Equipment costs created")


async def create_overhead_settings():
    """Create default overhead settings"""
    async with async_session_maker() as session:
        overhead = OverheadSettings(
            overhead_percent=Decimal("25.0"),
            profit_percent=Decimal("35.0"),
            safety_buffer_percent=Decimal("10.0"),
            vehicle_rate_per_mile=Decimal("0.65"),
            driver_hourly_rate=Decimal("25.00"),
            effective_date=datetime.utcnow().date(),
            created_by="system"
        )
        session.add(overhead)
        
        await session.commit()
        print("✅ Overhead settings created")


async def main():
    """Initialize the development database"""
    print("Initializing Tree Service Development Database...")
    print("=" * 60)
    
    try:
        # Create tables
        await create_tables()
        
        # Create test data
        await create_test_users()
        await create_labor_rates()
        await create_equipment_costs()
        await create_overhead_settings()
        
        print("\n✅ Database initialization complete!")
        print("\nTest Users Created:")
        print("  Admin:     admin / Admin123!")
        print("  Manager:   manager / Manager123!")
        print("  Estimator: estimator / Estimator123!")
        print("  Viewer:    viewer / Viewer123!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())