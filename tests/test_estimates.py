"""
Tests for estimates endpoints.
"""
import pytest
from httpx import AsyncClient
from datetime import date, timedelta
from decimal import Decimal

from src.models.user import User
from src.models.estimate import Estimate, EstimateStatus


class TestEstimateCreation:
    """Test estimate creation endpoint."""
    
    async def test_create_estimate_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful estimate creation."""
        estimate_data = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "customer_phone": "555-1234",
            "customer_address": "123 Main St",
            "job_address": "456 Oak Ave",
            "job_description": "Remove large oak tree",
            "scheduled_date": str(date.today() + timedelta(days=7)),
            "calculation_inputs": {
                "travel_hours": 1.5,
                "setup_hours": 2.0,
                "work_hours": 6.0,
                "num_crew": 3,
                "equipment_hours": 4.0,
                "equipment_list": ["chipper", "bucket_truck"],
                "disposal_trips": 2,
                "notes": "Large tree near power lines"
            }
        }
        
        response = await client.post(
            "/api/estimates",
            headers=auth_headers,
            json=estimate_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["customer_name"] == "John Doe"
        assert data["status"] == "DRAFT"
        assert "estimate_number" in data
        assert "total_price" in data
        assert float(data["total_price"]) > 0
    
    async def test_create_estimate_invalid_date(self, client: AsyncClient, auth_headers: dict):
        """Test estimate creation with past scheduled date."""
        estimate_data = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "customer_phone": "555-1234",
            "job_address": "456 Oak Ave",
            "job_description": "Remove tree",
            "scheduled_date": str(date.today() - timedelta(days=1)),  # Past date
            "calculation_inputs": {
                "work_hours": 4.0,
                "num_crew": 2
            }
        }
        
        response = await client.post(
            "/api/estimates",
            headers=auth_headers,
            json=estimate_data
        )
        assert response.status_code == 422
    
    async def test_create_estimate_missing_fields(self, client: AsyncClient, auth_headers: dict):
        """Test estimate creation with missing required fields."""
        estimate_data = {
            "customer_name": "John Doe",
            # Missing required fields
        }
        
        response = await client.post(
            "/api/estimates",
            headers=auth_headers,
            json=estimate_data
        )
        assert response.status_code == 422
    
    async def test_create_estimate_viewer_forbidden(self, client: AsyncClient, test_viewer: User):
        """Test that viewers cannot create estimates."""
        # Get viewer auth token
        login_response = await client.post(
            "/api/auth/login",
            data={
                "username": test_viewer.username,
                "password": "ViewerPassword123!"
            }
        )
        viewer_token = login_response.json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
        
        estimate_data = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "job_address": "456 Oak Ave",
            "job_description": "Remove tree",
            "scheduled_date": str(date.today() + timedelta(days=7)),
            "calculation_inputs": {"work_hours": 4.0, "num_crew": 2}
        }
        
        response = await client.post(
            "/api/estimates",
            headers=viewer_headers,
            json=estimate_data
        )
        assert response.status_code == 403


class TestEstimateRetrieval:
    """Test estimate retrieval endpoints."""
    
    @pytest.fixture
    async def sample_estimate(self, test_db, test_user) -> Estimate:
        """Create a sample estimate for testing."""
        estimate = Estimate(
            estimate_number="EST-2024-0001",
            customer_name="Test Customer",
            customer_email="customer@example.com",
            customer_phone="555-1234",
            customer_address="123 Test St",
            job_address="456 Job Ave",
            job_description="Test job",
            scheduled_date=date.today() + timedelta(days=7),
            calculation_inputs={"work_hours": 4.0, "num_crew": 2},
            calculation_result={
                "labor_cost": "200.00",
                "equipment_cost": "100.00",
                "total_cost": "500.00"
            },
            labor_cost=Decimal("200.00"),
            equipment_cost=Decimal("100.00"),
            vehicle_cost=Decimal("50.00"),
            disposal_cost=Decimal("50.00"),
            subtotal=Decimal("400.00"),
            overhead_amount=Decimal("100.00"),
            total_cost=Decimal("500.00"),
            safety_buffer_amount=Decimal("50.00"),
            profit_amount=Decimal("175.00"),
            total_price=Decimal("725.00"),
            status=EstimateStatus.DRAFT,
            valid_until=date.today() + timedelta(days=30),
            created_by=test_user.id
        )
        test_db.add(estimate)
        await test_db.commit()
        await test_db.refresh(estimate)
        return estimate
    
    async def test_get_estimate_by_id(self, client: AsyncClient, auth_headers: dict, sample_estimate: Estimate):
        """Test getting estimate by ID."""
        response = await client.get(
            f"/api/estimates/{sample_estimate.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_estimate.id
        assert data["estimate_number"] == sample_estimate.estimate_number
    
    async def test_get_nonexistent_estimate(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent estimate."""
        response = await client.get(
            "/api/estimates/99999",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_list_estimates(self, client: AsyncClient, auth_headers: dict, sample_estimate: Estimate):
        """Test listing estimates."""
        response = await client.get(
            "/api/estimates",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "estimates" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["estimates"]) >= 1
    
    async def test_list_estimates_with_filters(self, client: AsyncClient, auth_headers: dict, sample_estimate: Estimate):
        """Test listing estimates with filters."""
        response = await client.get(
            "/api/estimates",
            headers=auth_headers,
            params={
                "customer_name": "Test",
                "status": "DRAFT"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["estimates"]) >= 1
        assert all(e["status"] == "DRAFT" for e in data["estimates"])
    
    async def test_customer_view_no_auth(self, client: AsyncClient, sample_estimate: Estimate):
        """Test customer view without authentication."""
        response = await client.get(
            f"/api/estimates/{sample_estimate.id}/customer-view"
        )
        assert response.status_code == 200
        data = response.json()
        assert "estimate_number" in data
        assert "internal_notes" not in data  # Should not expose internal info


class TestEstimateUpdate:
    """Test estimate update endpoints."""
    
    async def test_update_draft_estimate(self, client: AsyncClient, auth_headers: dict, test_db, test_user):
        """Test updating a draft estimate."""
        # Create draft estimate
        estimate = Estimate(
            estimate_number="EST-2024-0002",
            customer_name="Original Name",
            customer_email="original@example.com",
            customer_phone="555-0000",
            job_address=!

<truncated>