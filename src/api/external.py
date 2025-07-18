"""
External API endpoints for integrating with third-party services.
"""
from typing import List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from src.api.deps import get_current_active_user
from src.models.user import User
from src.services.external_apis import (
    get_external_api_service,
    ExternalAPIService,
    TravelDistance,
    FuelPrice,
    ExternalAPIError,
    GoogleMapsError,
    FuelAPIError
)


router = APIRouter()


class DistanceRequest(BaseModel):
    """Request model for distance calculation."""
    origin: str = Field(..., description="Starting address")
    destination: str = Field(..., description="Destination address")
    departure_time: Optional[datetime] = Field(None, description="Departure time for traffic calculation")


class BatchDistanceRequest(BaseModel):
    """Request model for batch distance calculation."""
    origin: str = Field(..., description="Starting address")
    destinations: List[str] = Field(..., description="List of destination addresses", max_items=25)


class FuelPriceRequest(BaseModel):
    """Request model for fuel price lookup."""
    location: str = Field("local", description="Location identifier (zip code, city, or 'local')")
    fuel_type: str = Field("regular", description="Type of fuel (regular, premium, diesel)")


@router.post("/distance", response_model=TravelDistance)
async def calculate_distance(
    request: DistanceRequest,
    current_user: User = Depends(get_current_active_user),
    api_service: ExternalAPIService = Depends(get_external_api_service)
) -> Any:
    """
    Calculate travel distance and time between two addresses.
    
    Uses Google Maps Distance Matrix API with caching.
    """
    try:
        result = await api_service.calculate_travel_distance(
            origin=request.origin,
            destination=request.destination,
            departure_time=request.departure_time
        )
        return result
    except GoogleMapsError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Maps API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate distance: {str(e)}"
        )


@router.post("/distance/batch", response_model=List[TravelDistance])
async def calculate_batch_distances(
    request: BatchDistanceRequest,
    current_user: User = Depends(get_current_active_user),
    api_service: ExternalAPIService = Depends(get_external_api_service)
) -> Any:
    """
    Calculate distances from one origin to multiple destinations.
    
    Efficient batch processing for up to 25 destinations.
    """
    try:
        results = await api_service.calculate_multiple_distances(
            origin=request.origin,
            destinations=request.destinations
        )
        return results
    except GoogleMapsError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google Maps API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate distances: {str(e)}"
        )


@router.get("/fuel-price", response_model=FuelPrice)
async def get_fuel_price(
    location: str = Query("local", description="Location identifier"),
    fuel_type: str = Query("regular", description="Fuel type", regex="^(regular|premium|diesel)$"),
    current_user: User = Depends(get_current_active_user),
    api_service: ExternalAPIService = Depends(get_external_api_service)
) -> Any:
    """
    Get current fuel price for a location.
    
    Results are cached for 4 hours.
    """
    try:
        result = await api_service.get_current_fuel_price(
            location=location,
            fuel_type=fuel_type
        )
        return result
    except FuelAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fuel API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fuel price: {str(e)}"
        )


@router.get("/health")
async def check_external_apis_health(
    current_user: User = Depends(get_current_active_user),
    api_service: ExternalAPIService = Depends(get_external_api_service)
) -> Any:
    """
    Check health status of all external APIs.
    
    Returns status for each integrated service.
    """
    try:
        health_status = await api_service.get_api_health_status()
        
        # Calculate overall health
        all_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": health_status,
            "checked_at": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "error",
            "services": {
                "google_maps": False,
                "quickbooks": False,
                "fuel_api": False
            },
            "error": str(e),
            "checked_at": datetime.utcnow()
        }