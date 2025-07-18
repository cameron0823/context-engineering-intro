"""
Calculation schemas for request/response validation.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from src.core.config import settings


class CrewMember(BaseModel):
    """Schema for crew member in calculation."""
    role: str = Field(..., description="Role name (e.g., climber, groundsman)")
    hourly_rate: Decimal = Field(..., ge=0, decimal_places=2)
    
    @validator('hourly_rate')
    def quantize_rate(cls, v):
        """Ensure proper decimal precision."""
        return v.quantize(Decimal('0.01'))


class EquipmentItem(BaseModel):
    """Schema for equipment in calculation."""
    id: int = Field(..., description="Equipment ID")
    name: str = Field(..., description="Equipment name")
    hourly_cost: Decimal = Field(..., ge=0, decimal_places=2)
    
    @validator('hourly_cost')
    def quantize_cost(cls, v):
        """Ensure proper decimal precision."""
        return v.quantize(Decimal('0.01'))


class CalculationInput(BaseModel):
    """Schema for calculation input validation."""
    # Travel inputs
    travel_miles: Decimal = Field(..., ge=0, le=500, decimal_places=1)
    travel_time_minutes: int = Field(..., ge=0, le=600)  # Max 10 hours
    
    # Labor inputs
    crew_size: int = Field(..., ge=1, le=10)
    estimated_hours: Decimal = Field(..., ge=0.5, le=16, decimal_places=1)
    labor_rates: List[str] = Field(..., min_items=1, max_items=10)  # Role names
    
    # Equipment
    equipment_ids: List[int] = Field(default=[], max_items=20)
    
    # Job specifics
    disposal_fees: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    permit_cost: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    
    # Multipliers
    emergency_job: bool = Field(default=False)
    weekend_work: bool = Field(default=False)
    
    # Customer info (for estimate creation)
    customer_name: Optional[str] = Field(None, max_length=255)
    job_address: Optional[str] = Field(None, max_length=500)
    job_description: Optional[str] = Field(None, max_length=1000)
    
    @validator('travel_miles')
    def validate_reasonable_distance(cls, v):
        """Validate travel distance against settings."""
        max_miles = settings.MAX_TRAVEL_MILES
        if v > max_miles:
            raise ValueError(f"Travel distance exceeds maximum of {max_miles} miles")
        return v
    
    @validator('estimated_hours')
    def validate_reasonable_hours(cls, v):
        """Validate estimated hours against settings."""
        max_hours = settings.MAX_ESTIMATE_HOURS
        if v > max_hours:
            raise ValueError(f"Estimated hours exceeds maximum of {max_hours} hours")
        return v
    
    @validator('crew_size')
    def validate_crew_size(cls, v, values):
        """Validate crew size matches labor rates."""
        if 'labor_rates' in values and len(values['labor_rates']) != v:
            raise ValueError(f"Crew size ({v}) must match number of labor rates ({len(values['labor_rates'])})")
        return v
    
    @validator('disposal_fees', 'permit_cost')
    def quantize_fees(cls, v):
        """Ensure proper decimal precision."""
        return v.quantize(Decimal('0.01'))
    
    @validator('emergency_job')
    def validate_multipliers(cls, v, values):
        """Ensure only one multiplier is active."""
        if v and values.get('weekend_work', False):
            raise ValueError("Cannot have both emergency and weekend multipliers")
        return v


class TravelBreakdown(BaseModel):
    """Schema for travel cost breakdown."""
    mileage_cost: Decimal
    time_cost: Decimal
    total: Decimal
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class LaborBreakdown(BaseModel):
    """Schema for labor cost breakdown."""
    base_cost: Decimal
    multipliers_applied: Dict[str, str]
    total: Decimal
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class EquipmentBreakdown(BaseModel):
    """Schema for equipment cost breakdown."""
    itemized: Dict[str, Decimal]
    total: Decimal
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class FinalCalculation(BaseModel):
    """Schema for final calculation details."""
    direct_costs: Decimal
    overhead: Decimal
    overhead_percent: str
    safety_buffer: Decimal
    safety_buffer_percent: str
    profit: Decimal
    profit_percent: str
    subtotal: Decimal
    final_total: Decimal
    calculation_id: str
    timestamp: str
    formula_version: str
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class CalculationResult(BaseModel):
    """Schema for complete calculation result."""
    travel_breakdown: TravelBreakdown
    labor_breakdown: LaborBreakdown
    equipment_breakdown: EquipmentBreakdown
    disposal_fees: Decimal
    permit_cost: Decimal
    cost_components: Dict[str, Decimal]
    final_calculation: FinalCalculation
    calculation_checksum: str
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class QuickCalculationInput(BaseModel):
    """Schema for quick calculation without full details."""
    travel_miles: Decimal = Field(..., ge=0, le=500, decimal_places=1)
    estimated_hours: Decimal = Field(..., ge=0.5, le=16, decimal_places=1)
    crew_size: int = Field(..., ge=1, le=10)
    average_hourly_rate: Decimal = Field(..., ge=0, decimal_places=2)
    equipment_count: int = Field(default=0, ge=0, le=10)
    average_equipment_rate: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    
    @validator('average_hourly_rate', 'average_equipment_rate')
    def quantize_rates(cls, v):
        """Ensure proper decimal precision."""
        return v.quantize(Decimal('0.01'))


class CalculationComparisonInput(BaseModel):
    """Schema for comparing multiple calculation scenarios."""
    base_scenario: CalculationInput
    comparison_scenarios: List[CalculationInput] = Field(..., min_items=1, max_items=5)
    
    @validator('comparison_scenarios')
    def validate_scenario_count(cls, v):
        """Limit number of comparison scenarios."""
        if len(v) > 5:
            raise ValueError("Maximum 5 comparison scenarios allowed")
        return v


class HistoricalCalculationQuery(BaseModel):
    """Schema for querying historical calculations."""
    estimate_id: Optional[int] = None
    calculation_id: Optional[str] = None
    effective_date: Optional[datetime] = None
    
    @validator('calculation_id')
    def validate_uuid_format(cls, v):
        """Validate calculation ID is proper UUID format."""
        if v:
            try:
                import uuid
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Invalid calculation ID format")
        return v