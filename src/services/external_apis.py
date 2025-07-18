"""
External API integrations for the Tree Service Estimating application.

Includes:
- Google Maps Distance Matrix API for travel calculations
- QuickBooks API for invoice creation
- Fuel price API for current fuel costs
"""
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog
from pydantic import BaseModel, Field

from src.core.config import settings
try:
    from src.core.cache import get_cache
except ImportError:
    # Fallback if cache module has issues
    get_cache = None
from src.models.estimate import Estimate


logger = structlog.get_logger()


class TravelDistance(BaseModel):
    """Travel distance calculation result."""
    origin: str
    destination: str
    distance_miles: float
    duration_minutes: int
    distance_text: str
    duration_text: str
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class QuickBooksInvoice(BaseModel):
    """QuickBooks invoice creation result."""
    invoice_id: str
    invoice_number: str
    quickbooks_url: str
    created_at: datetime
    sync_token: str
    total_amount: Decimal


class FuelPrice(BaseModel):
    """Current fuel price data."""
    price_per_gallon: Decimal
    fuel_type: str = "regular"
    location: str
    last_updated: datetime
    source: str


class ExternalAPIError(Exception):
    """Base exception for external API errors."""
    pass


class GoogleMapsError(ExternalAPIError):
    """Google Maps API specific errors."""
    pass


class QuickBooksError(ExternalAPIError):
    """QuickBooks API specific errors."""
    pass


class FuelAPIError(ExternalAPIError):
    """Fuel price API specific errors."""
    pass


class ExternalAPIService:
    """
    Service for managing external API integrations.
    
    Handles:
    - Caching of API responses
    - Rate limiting
    - Error handling and retries
    - Response validation
    """
    
    def __init__(self):
        self.cache = get_cache() if get_cache else None
        self.google_maps_client = None
        self.quickbooks_client = None
        self.fuel_api_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize HTTP clients with appropriate timeouts and headers."""
        # Google Maps client
        self.google_maps_client = httpx.AsyncClient(
            base_url="https://maps.googleapis.com",
            timeout=httpx.Timeout(30.0),
            headers={"User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}"}
        )
        
        # QuickBooks client
        self.quickbooks_client = httpx.AsyncClient(
            base_url=settings.QUICKBOOKS_API_URL,
            timeout=httpx.Timeout(30.0),
            headers={
                "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
        
        # Fuel API client (example using a mock API - replace with actual)
        self.fuel_api_client = httpx.AsyncClient(
            base_url="https://api.fuelprices.com",  # Replace with actual API
            timeout=httpx.Timeout(10.0),
            headers={
                "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}",
                "X-API-Key": settings.FUEL_API_KEY
            }
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close all clients."""
        await self.close()
    
    async def close(self):
        """Close all HTTP clients."""
        if self.google_maps_client:
            await self.google_maps_client.aclose()
        if self.quickbooks_client:
            await self.quickbooks_client.aclose()
        if self.fuel_api_client:
            await self.fuel_api_client.aclose()
    
    # Google Maps Distance Matrix API
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def calculate_travel_distance(
        self,
        origin: str,
        destination: str,
        departure_time: Optional[datetime] = None
    ) -> TravelDistance:
        """
        Calculate travel distance and time using Google Maps Distance Matrix API.
        
        Args:
            origin: Starting address
            destination: Destination address
            departure_time: When to depart (for traffic calculations)
            
        Returns:
            TravelDistance object with miles and minutes
            
        Raises:
            GoogleMapsError: If API call fails
        """
        # Check cache first
        cache_key = f"distance:{origin}:{destination}"
        if self.cache:
            try:
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.info("Using cached distance calculation", origin=origin, destination=destination)
                    return TravelDistance(**cached)
            except Exception as e:
                logger.warning("Cache get failed", error=str(e))
        
        try:
            # Prepare API parameters
            params = {
                "origins": origin,
                "destinations": destination,
                "units": "imperial",
                "key": settings.GOOGLE_MAPS_API_KEY
            }
            
            if departure_time:
                params["departure_time"] = int(departure_time.timestamp())
                params["traffic_model"] = "best_guess"
            
            # Make API request
            response = await self.google_maps_client.get(
                "/maps/api/distancematrix/json",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Validate response
            if data["status"] != "OK":
                raise GoogleMapsError(f"API returned status: {data['status']}")
            
            if not data["rows"] or not data["rows"][0]["elements"]:
                raise GoogleMapsError("No route found")
            
            element = data["rows"][0]["elements"][0]
            
            if element["status"] != "OK":
                raise GoogleMapsError(f"Route status: {element['status']}")
            
            # Extract distance and duration
            distance_meters = element["distance"]["value"]
            distance_miles = distance_meters * 0.000621371  # Convert to miles
            duration_seconds = element["duration"]["value"]
            duration_minutes = duration_seconds // 60
            
            result = TravelDistance(
                origin=origin,
                destination=destination,
                distance_miles=round(distance_miles, 1),
                duration_minutes=duration_minutes,
                distance_text=element["distance"]["text"],
                duration_text=element["duration"]["text"]
            )
            
            # Cache the result for 24 hours
            if self.cache:
                try:
                    await self.cache.set(cache_key, result.model_dump(), expire=86400)
                except Exception as e:
                    logger.warning("Cache set failed", error=str(e))
            
            logger.info(
                "Calculated travel distance",
                origin=origin,
                destination=destination,
                miles=result.distance_miles,
                minutes=result.duration_minutes
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error("Google Maps API error", status_code=e.response.status_code, detail=e.response.text)
            raise GoogleMapsError(f"API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error calculating distance", error=str(e))
            raise GoogleMapsError(f"Failed to calculate distance: {str(e)}")
    
    # QuickBooks API Integration
    async def _get_quickbooks_token(self) -> str:
        """
        Get or refresh QuickBooks OAuth token.
        
        This is a simplified version - in production, you'd need proper OAuth flow.
        """
        # TODO: Implement proper OAuth2 token management
        # For now, assume token is stored in settings or cache
        if self.cache:
            try:
                cached_token = await self.cache.get("quickbooks:token")
                if cached_token:
                    return cached_token
            except Exception as e:
                logger.warning("Cache get failed for QB token", error=str(e))
        
        # In production, implement token refresh logic here
        raise QuickBooksError("QuickBooks token not available")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def create_quickbooks_invoice(
        self,
        estimate: Estimate,
        customer_id: Optional[str] = None
    ) -> QuickBooksInvoice:
        """
        Create an invoice in QuickBooks from an approved estimate.
        
        Args:
            estimate: Approved estimate to convert to invoice
            customer_id: QuickBooks customer ID (will create if not provided)
            
        Returns:
            QuickBooksInvoice object with invoice details
            
        Raises:
            QuickBooksError: If invoice creation fails
        """
        try:
            # Get authentication token
            token = await self._get_quickbooks_token()
            
            # Create or get customer
            if not customer_id:
                customer_id = await self._create_or_get_quickbooks_customer(estimate, token)
            
            # Prepare invoice data
            invoice_data = {
                "Line": [
                    {
                        "Description": estimate.job_description,
                        "Amount": float(estimate.final_total),
                        "DetailType": "SalesItemLineDetail",
                        "SalesItemLineDetail": {
                            "ItemRef": {
                                "value": "1",  # Default service item - configure in settings
                                "name": "Tree Service"
                            }
                        }
                    }
                ],
                "CustomerRef": {
                    "value": customer_id
                },
                "BillEmail": {
                    "Address": estimate.customer_email
                },
                "DueDate": (date.today() + timedelta(days=30)).isoformat(),
                "PrivateNote": f"Estimate #{estimate.estimate_number}",
                "CustomerMemo": {
                    "value": estimate.customer_notes or ""
                }
            }
            
            # Add line items for cost breakdown if needed
            if estimate.calculation_result:
                breakdown = [
                    ("Labor", estimate.labor_cost),
                    ("Equipment", estimate.equipment_cost),
                    ("Travel", estimate.travel_cost),
                    ("Disposal Fees", estimate.disposal_fees),
                    ("Permits", estimate.permit_cost)
                ]
                
                for description, amount in breakdown:
                    if amount and amount > 0:
                        invoice_data["Line"].append({
                            "Description": description,
                            "Amount": float(amount),
                            "DetailType": "DescriptionOnly"
                        })
            
            # Create invoice
            response = await self.quickbooks_client.post(
                f"/v3/company/{settings.QUICKBOOKS_COMPANY_ID}/invoice",
                json=invoice_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            
            invoice = response.json()["Invoice"]
            
            result = QuickBooksInvoice(
                invoice_id=invoice["Id"],
                invoice_number=invoice["DocNumber"],
                quickbooks_url=f"{settings.QUICKBOOKS_API_URL}/app/invoice?txnId={invoice['Id']}",
                created_at=datetime.utcnow(),
                sync_token=invoice["SyncToken"],
                total_amount=Decimal(str(invoice["TotalAmt"]))
            )
            
            logger.info(
                "Created QuickBooks invoice",
                estimate_id=estimate.id,
                invoice_id=result.invoice_id,
                amount=result.total_amount
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error("QuickBooks API error", status_code=e.response.status_code, detail=e.response.text)
            raise QuickBooksError(f"Failed to create invoice: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error creating invoice", error=str(e))
            raise QuickBooksError(f"Failed to create invoice: {str(e)}")
    
    async def _create_or_get_quickbooks_customer(
        self,
        estimate: Estimate,
        token: str
    ) -> str:
        """
        Create or retrieve QuickBooks customer ID.
        
        Args:
            estimate: Estimate with customer info
            token: OAuth token
            
        Returns:
            QuickBooks customer ID
        """
        # First, try to find existing customer by email
        query = f"SELECT * FROM Customer WHERE PrimaryEmailAddr = '{estimate.customer_email}'"
        
        response = await self.quickbooks_client.get(
            f"/v3/company/{settings.QUICKBOOKS_COMPANY_ID}/query",
            params={"query": query},
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        
        customers = response.json().get("QueryResponse", {}).get("Customer", [])
        
        if customers:
            return customers[0]["Id"]
        
        # Create new customer
        customer_data = {
            "DisplayName": estimate.customer_name,
            "PrimaryEmailAddr": {
                "Address": estimate.customer_email
            },
            "PrimaryPhone": {
                "FreeFormNumber": estimate.customer_phone
            }
        }
        
        if estimate.customer_address:
            # Parse address if structured
            customer_data["BillAddr"] = {
                "Line1": estimate.customer_address,
                "City": "",  # Would need to parse from address
                "CountrySubDivisionCode": "",  # State
                "PostalCode": ""
            }
        
        response = await self.quickbooks_client.post(
            f"/v3/company/{settings.QUICKBOOKS_COMPANY_ID}/customer",
            json=customer_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        
        return response.json()["Customer"]["Id"]
    
    # Fuel Price API Integration
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def get_current_fuel_price(
        self,
        location: str = "local",
        fuel_type: str = "regular"
    ) -> FuelPrice:
        """
        Get current fuel price for a location.
        
        Args:
            location: Location identifier (zip code, city, or "local")
            fuel_type: Type of fuel (regular, diesel, premium)
            
        Returns:
            FuelPrice object with current price
            
        Raises:
            FuelAPIError: If API call fails
        """
        # Check cache first (cache for 4 hours)
        cache_key = f"fuel:{location}:{fuel_type}"
        if self.cache:
            try:
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.info("Using cached fuel price", location=location, fuel_type=fuel_type)
                    return FuelPrice(**cached)
            except Exception as e:
                logger.warning("Cache get failed", error=str(e))
        
        try:
            # This is a mock implementation - replace with actual fuel API
            # Some options: GasBuddy API, EIA.gov API, or commercial providers
            
            # For demonstration, using a simple calculation
            base_prices = {
                "regular": Decimal("3.50"),
                "premium": Decimal("4.00"),
                "diesel": Decimal("4.25")
            }
            
            # In production, make actual API call here
            # response = await self.fuel_api_client.get(
            #     f"/v1/prices",
            #     params={"location": location, "fuel_type": fuel_type}
            # )
            # response.raise_for_status()
            # data = response.json()
            
            # Mock response
            result = FuelPrice(
                price_per_gallon=base_prices.get(fuel_type, base_prices["regular"]),
                fuel_type=fuel_type,
                location=location,
                last_updated=datetime.utcnow(),
                source="mock_api"  # Replace with actual source
            )
            
            # Cache the result
            if self.cache:
                try:
                    await self.cache.set(cache_key, result.model_dump(), expire=14400)  # 4 hours
                except Exception as e:
                    logger.warning("Cache set failed", error=str(e))
            
            logger.info(
                "Retrieved fuel price",
                location=location,
                fuel_type=fuel_type,
                price=result.price_per_gallon
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error("Fuel API error", status_code=e.response.status_code, detail=e.response.text)
            raise FuelAPIError(f"Failed to get fuel price: {e.response.status_code}")
        except Exception as e:
            logger.error("Unexpected error getting fuel price", error=str(e))
            raise FuelAPIError(f"Failed to get fuel price: {str(e)}")
    
    # Batch operations for efficiency
    async def calculate_multiple_distances(
        self,
        origin: str,
        destinations: List[str]
    ) -> List[TravelDistance]:
        """
        Calculate distances to multiple destinations efficiently.
        
        Args:
            origin: Starting address
            destinations: List of destination addresses
            
        Returns:
            List of TravelDistance objects
        """
        # Google Maps Distance Matrix API supports up to 25 destinations per request
        results = []
        
        for i in range(0, len(destinations), 25):
            batch = destinations[i:i + 25]
            batch_destinations = "|".join(batch)
            
            # Check cache for batch
            cache_key = f"batch_distance:{origin}:{hash(batch_destinations)}"
            cached = None
            if self.cache:
                try:
                    cached = await self.cache.get(cache_key)
                except Exception as e:
                    logger.warning("Cache get failed", error=str(e))
            
            if cached:
                results.extend([TravelDistance(**d) for d in cached])
                continue
            
            try:
                params = {
                    "origins": origin,
                    "destinations": batch_destinations,
                    "units": "imperial",
                    "key": settings.GOOGLE_MAPS_API_KEY
                }
                
                response = await self.google_maps_client.get(
                    "/maps/api/distancematrix/json",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data["status"] != "OK":
                    logger.error("Batch distance calculation failed", status=data["status"])
                    continue
                
                batch_results = []
                for idx, element in enumerate(data["rows"][0]["elements"]):
                    if element["status"] == "OK":
                        distance_miles = element["distance"]["value"] * 0.000621371
                        duration_minutes = element["duration"]["value"] // 60
                        
                        result = TravelDistance(
                            origin=origin,
                            destination=batch[idx],
                            distance_miles=round(distance_miles, 1),
                            duration_minutes=duration_minutes,
                            distance_text=element["distance"]["text"],
                            duration_text=element["duration"]["text"]
                        )
                        batch_results.append(result)
                
                # Cache batch results
                if self.cache:
                    try:
                        await self.cache.set(
                            cache_key,
                            [r.model_dump() for r in batch_results],
                            expire=86400
                        )
                    except Exception as e:
                        logger.warning("Cache set failed", error=str(e))
                
                results.extend(batch_results)
                
            except Exception as e:
                logger.error("Batch distance calculation error", error=str(e))
                # Continue with next batch
        
        return results
    
    # Health check methods
    async def check_google_maps_health(self) -> bool:
        """Check if Google Maps API is accessible."""
        try:
            response = await self.google_maps_client.get(
                "/maps/api/distancematrix/json",
                params={
                    "origins": "New York, NY",
                    "destinations": "Boston, MA",
                    "key": settings.GOOGLE_MAPS_API_KEY
                },
                timeout=5.0
            )
            return response.status_code == 200
        except:
            return False
    
    async def check_quickbooks_health(self) -> bool:
        """Check if QuickBooks API is accessible."""
        try:
            # Simple health check - actual implementation would verify OAuth
            response = await self.quickbooks_client.get(
                "/v3/company/{companyId}/companyinfo",
                timeout=5.0
            )
            return response.status_code in [200, 401]  # 401 is expected without auth
        except:
            return False
    
    async def check_fuel_api_health(self) -> bool:
        """Check if Fuel API is accessible."""
        # Mock implementation - always return True
        return True
    
    async def get_api_health_status(self) -> Dict[str, bool]:
        """Get health status of all external APIs."""
        results = await asyncio.gather(
            self.check_google_maps_health(),
            self.check_quickbooks_health(),
            self.check_fuel_api_health(),
            return_exceptions=True
        )
        
        return {
            "google_maps": results[0] if isinstance(results[0], bool) else False,
            "quickbooks": results[1] if isinstance(results[1], bool) else False,
            "fuel_api": results[2] if isinstance(results[2], bool) else False
        }


# Singleton instance
_external_api_service: Optional[ExternalAPIService] = None


def get_external_api_service() -> ExternalAPIService:
    """Get or create the external API service singleton."""
    global _external_api_service
    if _external_api_service is None:
        _external_api_service = ExternalAPIService()
    return _external_api_service