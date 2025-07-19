"""
Tests for database models.
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from src.models.user import User, UserRole
from src.models.estimate import Estimate, EstimateStatus
from src.models.costs import LaborRate, EquipmentCost, OverheadSettings
from src.models.audit import AuditLog


class TestUserModel:
    """Test User model functionality."""
    
    async def test_create_user(self, test_db):
        """Test creating a user."""
        user = User(
            username="testuser123",
            email="test123@example.com",
            full_name="Test User 123",
            phone_number="555-9999",
            department="Engineering",
            hashed_password="hashed_password_here",
            role=UserRole.ESTIMATOR
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser123"
        assert user.role == UserRole.ESTIMATOR
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
    
    async def test_user_unique_constraints(self, test_db):
        """Test unique constraints on username and email."""
        user1 = User(
            username="unique_user",
            email="unique@example.com",
            full_name="User 1",
            hashed_password="hash1"
        )
        test_db.add(user1)
        await test_db.commit()
        
        # Try to create user with same username
        user2 = User(
            username="unique_user",  # Duplicate
            email="different@example.com",
            full_name="User 2",
            hashed_password="hash2"
        )
        test_db.add(user2)
        
        with pytest.raises(IntegrityError):
            await test_db.commit()
        
        await test_db.rollback()
        
        # Try to create user with same email
        user3 = User(
            username="different_user",
            email="unique@example.com",  # Duplicate
            full_name="User 3",
            hashed_password="hash3"
        )
        test_db.add(user3)
        
        with pytest.raises(IntegrityError):
            await test_db.commit()
    
    async def test_user_permissions(self, test_db):
        """Test user permission checking."""
        admin = User(
            username="admin_user",
            email="admin@example.com",
            full_name="Admin User",
            hashed_password="hash",
            role=UserRole.ADMIN
        )
        
        estimator = User(
            username="estimator_user",
            email="estimator@example.com",
            full_name="Estimator User",
            hashed_password="hash",
            role=UserRole.ESTIMATOR
        )
        
        viewer = User(
            username="viewer_user",
            email="viewer@example.com",
            full_name="Viewer User",
            hashed_password="hash",
            role=UserRole.VIEWER
        )
        
        # Test permissions
        assert admin.has_permission("costs:write") is True
        assert admin.has_permission("estimates:approve") is True
        
        assert estimator.has_permission("estimates:write") is True
        assert estimator.has_permission("costs:write") is False
        
        assert viewer.has_permission("estimates:read") is True
        assert viewer.has_permission("estimates:write") is False
    
    async def test_soft_delete(self, test_db, test_user):
        """Test soft delete functionality."""
        assert test_user.deleted_at is None
        
        # Soft delete the user
        test_user.deleted_at = datetime.utcnow()
        test_user.deleted_by = "admin"
        await test_db.commit()
        
        assert test_user.deleted_at is not None
        assert test_user.deleted_by == "admin"


class TestEstimateModel:
    """Test Estimate model functionality."""
    
    async def test_create_estimate(self, test_db, test_user):
        """Test creating an estimate."""
        estimate = Estimate(
            estimate_number="EST-2024-0001",
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_phone="555-1234",
            customer_address="123 Main St",
            job_address="456 Oak Ave",
            job_description="Remove large oak tree",
            scheduled_date=date.today() + timedelta(days=7),
            calculation_inputs={"work_hours": 4.0, "num_crew": 2},
            calculation_result={"total": 1000.00},
            labor_cost=Decimal("400.00"),
            equipment_cost=Decimal("200.00"),
            vehicle_cost=Decimal("100.00"),
            disposal_cost=Decimal("50.00"),
            subtotal=Decimal("750.00"),
            overhead_amount=Decimal("187.50"),
            total_cost=Decimal("937.50"),
            profit_amount=Decimal("328.13"),
            total_price=Decimal("1265.00"),
            status=EstimateStatus.DRAFT,
            valid_until=date.today() + timedelta(days=30),
            created_by=test_user.id
        )
        test_db.add(estimate)
        await test_db.commit()
        await test_db.refresh(estimate)
        
        assert estimate.id is not None
        assert estimate.estimate_number == "EST-2024-0001"
        assert estimate.status == EstimateStatus.DRAFT
        assert estimate.is_editable() is True
        assert estimate.is_valid() is True
    
    async def test_estimate_status_transitions(self, test_db, test_user, test_admin):
        """Test estimate status transitions."""
        estimate = Estimate(
            estimate_number="EST-2024-0002",
            customer_name="Jane Doe",
            customer_email="jane@example.com",
            customer_phone="555-5678",
            job_address="789 Pine St",
            job_description="Trim hedges",
            scheduled_date=date.today() + timedelta(days=3),
            calculation_inputs={},
            calculation_result={},
            total_price=Decimal("500.00"),
            status=EstimateStatus.DRAFT,
            valid_until=date.today() + timedelta(days=30),
            created_by=test_user.id
        )
        test_db.add(estimate)
        await test_db.commit()
        
        # Draft can be edited
        assert estimate.is_editable() is True
        assert estimate.can_approve() is False
        
        # Move to pending
        estimate.status = EstimateStatus.PENDING
        await test_db.commit()
        
        assert estimate.is_editable() is True
        assert estimate.can_approve() is True
        
        # Approve
        estimate.status = EstimateStatus.APPROVED
        estimate.approved_by = test_admin.id
        estimate.approved_at = datetime.utcnow()
        await test_db.commit()
        
        assert estimate.is_editable() is False
        assert estimate.can_approve() is False
        assert estimate.can_invoice() is True
    
    async def test_estimate_validity(self, test_db, test_user):
        """Test estimate validity checking."""
        # Create expired estimate
        estimate = Estimate(
            estimate_number="EST-2024-0003",
            customer_name="Expired Customer",
            customer_email="expired@example.com",
            customer_phone="555-0000",
            job_address="999 Old St",
            job_description="Old job",
            scheduled_date=date.today() - timedelta(days=30),
            calculation_inputs={},
            calculation_result={},
            total_price=Decimal("300.00"),
            status=EstimateStatus.PENDING,
            valid_until=date.today() - timedelta(days=1),  # Expired
            created_by=test_user.id
        )
        test_db.add(estimate)
        await test_db.commit()
        
        assert estimate.is_valid() is False
        
        # Expired estimates cannot be approved
        assert estimate.can_approve() is False


class TestCostModels:
    """Test cost-related models."""
    
    async def test_labor_rate_effective_dating(self, test_db, test_user):
        """Test labor rate with effective dating."""
        # Current rate
        current_rate = LaborRate(
            role="Crew Member",
            hourly_rate=Decimal("50.00"),
            overtime_multiplier=Decimal("1.5"),
            weekend_multiplier=Decimal("2.0"),
            emergency_multiplier=Decimal("3.0"),
            effective_from=date.today() - timedelta(days=30),
            effective_to=date.today() + timedelta(days=30),
            is_active=True,
            created_by=test_user.id
        )
        test_db.add(current_rate)
        
        # Future rate
        future_rate = LaborRate(
            role="Crew Member",
            hourly_rate=Decimal("55.00"),
            overtime_multiplier=Decimal("1.5"),
            weekend_multiplier=Decimal("2.0"),
            emergency_multiplier=Decimal("3.0"),
            effective_from=date.today() + timedelta(days=31),
            effective_to=None,
            is_active=True,
            created_by=test_user.id
        )
        test_db.add(future_rate)
        
        await test_db.commit()
        
        assert current_rate.hourly_rate == Decimal("50.00")
        assert future_rate.hourly_rate == Decimal("55.00")
    
    async def test_equipment_cost(self, test_db, test_user):
        """Test equipment cost model."""
        equipment = EquipmentCost(
            equipment_name="Wood Chipper",
            equipment_type="chipper",
            model="CH-2000",
            hourly_rate=Decimal("75.00"),
            daily_rate=Decimal("500.00"),
            fuel_cost_per_hour=Decimal("15.00"),
            maintenance_cost_per_hour=Decimal("10.00"),
            is_available=True,
            maintenance_due_date=date.today() + timedelta(days=90),
            effective_from=date.today(),
            created_by=test_user.id
        )
        test_db.add(equipment)
        await test_db.commit()
        
        assert equipment.total_hourly_cost == Decimal("100.00")  # 75 + 15 + 10
        assert equipment.needs_maintenance is False
        
        # Set maintenance due in past
        equipment.maintenance_due_date = date.today() - timedelta(days=1)
        await test_db.commit()
        
        assert equipment.needs_maintenance is True
    
    async def test_overhead_settings(self, test_db, test_user):
        """Test overhead settings model."""
        settings = OverheadSettings(
            setting_name="Standard",
            overhead_percent=Decimal("25.0"),
            profit_percent=Decimal("35.0"),
            safety_buffer_percent=Decimal("10.0"),
            is_default=True,
            effective_from=date.today(),
            created_by=test_user.id
        )
        test_db.add(settings)
        await test_db.commit()
        
        assert settings.overhead_percent == Decimal("25.0")
        assert settings.profit_percent == Decimal("35.0")
        assert settings.safety_buffer_percent == Decimal("10.0")
        assert settings.is_default is True


class TestAuditLog:
    """Test audit log functionality."""
    
    async def test_audit_log_creation(self, test_db, test_user):
        """Test creating audit log entries."""
        audit_log = AuditLog(
            table_name="users",
            record_id=test_user.id,
            action="UPDATE",
            user_id=test_user.id,
            old_values={"email": "old@example.com"},
            new_values={"email": "new@example.com"},
            changed_fields=["email"],
            ip_address="127.0.0.1",
            user_agent="Test/1.0"
        )
        test_db.add(audit_log)
        await test_db.commit()
        
        assert audit_log.audit_id is not None
        assert audit_log.table_name == "users"
        assert audit_log.action == "UPDATE"
        assert "email" in audit_log.changed_fields
        assert audit_log.created_at is not None