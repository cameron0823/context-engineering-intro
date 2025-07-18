"""
Tests for external API integrations.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.services.external_apis import (
    ExternalAPIService,
    TravelDistance,
    FuelPrice,
    QuickBooksInvoice,
    GoogleMapsError,
    QuickBooksError,
    FuelAPIError
)
from src.models.estimate import Estimate, EstimateStatus


@pytest.fixture
async def api_service():
    """Create an external API service instance for testing."""
    service = ExternalAPIService()
    yield service
    await service.close()


@pytest.fixture
def mock_cache():
    """Create a mock cache."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def sample_estimate():
    """Create a sample estimate for testing."""
    estimate = MagicMock(spec=Estimate)
    estimate.id = 1
    estimate.estimate_number = "EST-20240117-0001"
    estimate.customer_name = "John Doe"
    estimate.customer_email = "john@example.com"
    estimate.customer_phone = "555-1234"
    estimate.customer_address = "123 Main St, Anytown, USA"
    estimate.job_description = "Tree removal service"
    estimate.final_total = Decimal("1500.00")
    estimate.labor_cost = Decimal("800.00")
    estimate.equipment_cost = Decimal("300.00")
    estimate.travel_cost = Decimal("100.00")
    estimate.disposal_fees = Decimal("200.00")
    estimate.permit_cost = Decimal("100.00")
    estimate.customer_notes = "Please be careful with the garden"
    estimate.calculation_result = {
        "total_breakdown": "Detailed breakdown here"
    }
    estimate.status = EstimateStatus.APPROVED
    return estimate


class TestGoogleMapsIntegration:
    """Test Google Maps Distance Matrix API integration."""
    
    @pytest.mark.asyncio
    async def test_calculate_travel_distance_success(self, api_service, mock_cache):
        """Test successful distance calculation."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {
                        "value": 16093,  # 10 miles in meters
                        "text": "10 mi"
                    },
                    "duration": {
                        "value": 900,  # 15 minutes in seconds
                        "text": "15 mins"
                    }
                }]
            }]
        }
        
        with patch.object(api_service, 'cache', mock_cache):
            with patch.object(api_service.google_maps_client, 'get', 
                            return_value=mock_response) as mock_get:
                result = await api_service.calculate_travel_distance(
                    origin="123 Main St",
                    destination="456 Oak Ave"
                )
        
        assert isinstance(result, TravelDistance)
        assert result.distance_miles == 10.0
        assert result.duration_minutes == 15
        assert result.distance_text == "10 mi"
        assert result.duration_text == "15 mins"
        
        # Verify cache was checked and set
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_travel_distance_cached(self, api_service, mock_cache):
        """Test distance calculation with cached result."""
        cached_data = {
            "origin": "123 Main St",
            "destination": "456 Oak Ave",
            "distance_miles": 10.0,
            "duration_minutes": 15,
            "distance_text": "10 mi",
            "duration_text": "15 mins",
            "calculated_at": datetime.utcnow().isoformat()
        }
        mock_cache.get.return_value = cached_data
        
        with patch.object(api_service, 'cache', mock_cache):
            result = await api_service.calculate_travel_distance(
                origin="123 Main St",
                destination="456 Oak Ave"
            )
        
        assert result.distance_miles == 10.0
        assert result.duration_minutes == 15
        
        # Verify no API call was made
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_calculate_travel_distance_api_error(self, api_service, mock_cache):
        """Test handling of Google Maps API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "REQUEST_DENIED",
            "error_message": "Invalid API key"
        }
        
        with patch.object(api_service, 'cache', mock_cache):
            with patch.object(api_service.google_maps_client, 'get',
                            return_value=mock_response):
                with pytest.raises(GoogleMapsError) as exc_info:
                    await api_service.calculate_travel_distance(
                        origin="123 Main St",
                        destination="456 Oak Ave"
                    )
        
        assert "REQUEST_DENIED" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_calculate_multiple_distances(self, api_service, mock_cache):
        """Test batch distance calculation."""
        destinations = ["456 Oak Ave", "789 Pine St", "321 Elm Rd"]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{
                "elements": [
                    {
                        "status": "OK",
                        "distance": {"value": 16093, "text": "10 mi"},
                        "duration": {"value": 900, "text": "15 mins"}
                    },
                    {
                        "status": "OK",
                        "distance": {"value": 24140, "text": "15 mi"},
                        "duration": {"value": 1200, "text": "20 mins"}
                    },
                    {
                        "status": "OK",
                        "distance": {"value": 8047, "text": "5 mi"},
                        "duration": {"value": 600, "text": "10 mins"}
                    }
                ]
            }]
        }
        
        with patch.object(api_service, 'cache', mock_cache):
            with patch.object(api_service.google_maps_client, 'get',
                            return_value=mock_response):
                results = await api_service.calculate_multiple_distances(
                    origin="123 Main St",
                    destinations=destinations
                )
        
        assert len(results) == 3
        assert results[0].distance_miles == 10.0
        assert results[1].distance_miles == 15.0
        assert results[2].distance_miles == 5.0


class TestQuickBooksIntegration:
    """Test QuickBooks API integration."""
    
    @pytest.mark.asyncio
    async def test_create_invoice_success(self, api_service, sample_estimate, mock_cache):
        """Test successful invoice creation."""
        # Mock token retrieval
        with patch.object(api_service, '_get_quickbooks_token',
                         return_value="test_token"):
            # Mock customer search
            customer_response = MagicMock()
            customer_response.status_code = 200
            customer_response.json.return_value = {
                "QueryResponse": {
                    "Customer": [{
                        "Id": "123",
                        "DisplayName": "John Doe"
                    }]
                }
            }
            
            # Mock invoice creation
            invoice_response = MagicMock()
            invoice_response.status_code = 200
            invoice_response.json.return_value = {
                "Invoice": {
                    "Id": "INV-001",
                    "DocNumber": "1001",
                    "SyncToken": "0",
                    "TotalAmt": 1500.00
                }
            }
            
            with patch.object(api_service, 'cache', mock_cache):
                with patch.object(api_service.quickbooks_client, 'get',
                                return_value=customer_response):
                    with patch.object(api_service.quickbooks_client, 'post',
                                    return_value=invoice_response):
                        result = await api_service.create_quickbooks_invoice(
                            sample_estimate
                        )
        
        assert isinstance(result, QuickBooksInvoice)
        assert result.invoice_id == "INV-001"
        assert result.invoice_number == "1001"
        assert result.total_amount == Decimal("1500.00")
    
    @pytest.mark.asyncio
    async def test_create_invoice_new_customer(self, api_service, sample_estimate, mock_cache):
        """Test invoice creation with new customer."""
        with patch.object(api_service, '_get_quickbooks_token',
                         return_value="test_token"):
            # Mock customer search - no results
            search_response = MagicMock()
            search_response.status_code = 200
            search_response.json.return_value = {
                "QueryResponse": {}
            }
            
            # Mock customer creation
            customer_response = MagicMock()
            customer_response.status_code = 200
            customer_response.json.return_value = {
                "Customer": {
                    "Id": "124",
                    "DisplayName": "John Doe"
                }
            }
            
            # Mock invoice creation
            invoice_response = MagicMock()
            invoice_response.status_code = 200
            invoice_response.json.return_value = {
                "Invoice": {
                    "Id": "INV-002",
                    "DocNumber": "1002",
                    "SyncToken": "0",
                    "TotalAmt": 1500.00
                }
            }
            
            with patch.object(api_service, 'cache', mock_cache):
                with patch.object(api_service.quickbooks_client, 'get',
                                return_value=search_response):
                    with patch.object(api_service.quickbooks_client, 'post',
                                    side_effect=[customer_response, invoice_response]):
                        result = await api_service.create_quickbooks_invoice(
                            sample_estimate
                        )
        
        assert result.invoice_id == "INV-002"
    
    @pytest.mark.asyncio
    async def test_create_invoice_api_error(self, api_service, sample_estimate, mock_cache):
        """Test handling of QuickBooks API errors."""
        with patch.object(api_service, '_get_quickbooks_token',
                         side_effect=QuickBooksError("Token not available")):
            with pytest.raises(QuickBooksError) as exc_info:
                await api_service.create_quickbooks_invoice(sample_estimate)
        
        assert "Token not available" in str(exc_info.value)


class TestFuelPriceIntegration:
    """Test fuel price API integration."""
    
    @pytest.mark.asyncio
    async def test_get_fuel_price_success(self, api_service, mock_cache):
        """Test successful fuel price retrieval."""
        with patch.object(api_service, 'cache', mock_cache):
            result = await api_service.get_current_fuel_price(
                location="local",
                fuel_type="regular"
            )
        
        assert isinstance(result, FuelPrice)
        assert result.price_per_gallon == Decimal("3.50")
        assert result.fuel_type == "regular"
        assert result.location == "local"
        assert result.source == "mock_api"
        
        # Verify cache was set
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_fuel_price_cached(self, api_service, mock_cache):
        """Test fuel price retrieval with cached result."""
        cached_data = {
            "price_per_gallon": "3.75",
            "fuel_type": "premium",
            "location": "12345",
            "last_updated": datetime.utcnow().isoformat(),
            "source": "cache"
        }
        mock_cache.get.return_value = cached_data
        
        with patch.object(api_service, 'cache', mock_cache):
            result = await api_service.get_current_fuel_price(
                location="12345",
                fuel_type="premium"
            )
        
        assert result.price_per_gallon == Decimal("3.75")
        assert result.source == "cache"
        
        # Verify no API call was made
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()


class TestHealthChecks:
    """Test API health check functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, api_service):
        """Test health check when all APIs are healthy."""
        with patch.object(api_service, 'check_google_maps_health',
                         return_value=True):
            with patch.object(api_service, 'check_quickbooks_health',
                             return_value=True):
                with patch.object(api_service, 'check_fuel_api_health',
                                 return_value=True):
                    health_status = await api_service.get_api_health_status()
        
        assert health_status["google_maps"] is True
        assert health_status["quickbooks"] is True
        assert health_status["fuel_api"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_partial_failure(self, api_service):
        """Test health check with partial API failures."""
        with patch.object(api_service, 'check_google_maps_health',
                         return_value=True):
            with patch.object(api_service, 'check_quickbooks_health',
                             return_value=False):
                with patch.object(api_service, 'check_fuel_api_health',
                                 return_value=True):
                    health_status = await api_service.get_api_health_status()
        
        assert health_status["google_maps"] is True
        assert health_status["quickbooks"] is False
        assert health_status["fuel_api"] is True