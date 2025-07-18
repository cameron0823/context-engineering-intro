"""
Cost management schemas for request/response validation.
"""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class LaborRateBase(BaseModel):
    """Base schema for labor rates."""
    role: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    hourly_rate: Decimal = Field(..., ge=0, decimal_places=2)
    overtime_multiplier: Decimal = Field(default=Decimal("1.5"), ge=1, decimal_places=2)
    weekend_multiplier: Decimal = Field(default=Decimal("2.0"), ge=1, decimal_places=2)
    emergency_multiplier: Decimal = Field(default=Decimal("2.5"), ge=1, decimal_places=2)
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('effective_to')
    def validate_effective_to(cls, v, values):
        """Ensure effective_to is after effective_from."""
        if v and 'effective_from' in values and v <= values['effective_from']:
            raise ValueError('effective_to must be after effective_from')
        return v
    
    @validator('hourly_rate', 'overtime_multiplier', 'weekend_multiplier', 'emergency_multiplier')
    def quantize_decimals(cls, v):
        """Ensure proper decimal precision."""
        return v.quantize(Decimal('0.01'))


class LaborRateCreate(LaborRateBase):
    """Schema for creating a labor rate."""
    pass


class LaborRateUpdate(BaseModel):
    """Schema for updating a labor rate."""
    description: Optional[str] = Field(None, max_length=255)
    hourly_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    overtime_multiplier: Optional[Decimal] = Field(None, ge=1, decimal_places=2)
    weekend_multiplier: Optional[Decimal] = Field(None, ge=1, decimal_places=2)
    emergency_multiplier: Optional[Decimal] = Field(None, ge=1, decimal_places=2)
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('hourly_rate', 'overtime_multiplier', 'weekend_multiplier', 'emergency_multiplier')
    def quantize_decimals(cls, v):
        """Ensure proper decimal precision."""
        if v is not None:
            return v.quantize(Decimal('0.01'))
        return v


class LaborRateResponse(LaborRateBase):
    """Schema for labor rate responses."""
    id: int
    is_current: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


class EquipmentCostBase(BaseModel):
    """Base schema for equipment costs."""
    equipment_name: str = Field(..., min_length=1, max_length=100)
    equipment_type: str = Field(..., min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    hourly_rate: Decimal = Field(..., ge=0, decimal_places=2)
    daily_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    fuel_cost_per_hour: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    maintenance_cost_per_hour: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    is_available: bool = True
    maintenance_due_date: Optional[date] = None
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('effective_to')
    def validate_effective_to(cls, v, values):
        """Ensure effective_to is after effective_from."""
        if v and 'effective_from' in values and v <= values['effective_from']:
            raise ValueError('effective_to must be after effective_from')
        return v


class EquipmentCostCreate(EquipmentCostBase):
    """Schema for creating equipment cost."""
    pass


class EquipmentCostUpdate(BaseModel):
    """Schema for updating equipment cost."""
    equipment_name: Optional[str] = Field(None, min_length=1, max_length=100)
    equipment_type: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    hourly_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    daily_rate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    fuel_cost_per_hour: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    maintenance_cost_per_hour: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_available: Optional[bool] = None
    maintenance_due_date: Optional[date] = None
    effective_to: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class EquipmentCostResponse(EquipmentCostBase):
    """Schema for equipment cost responses."""
    id: int
    total_hourly_cost: Decimal
    needs_maintenance: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


class OverheadSettingsBase(BaseModel):
    """Base schema for overhead settings."""
    setting_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    overhead_percent: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    profit_percent: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    safety_buffer_percent: Decimal = Field(default=Decimal("10.0"), ge=0, le=100, decimal_places=2)
    effective_from: date
    effective_to: Optional[date] = None
    is_default: bool = False
    is_active: bool = True
    
    @validator('effective_to')
    def validate_effective_to(cls, v, values):
        """Ensure effective_to is after effective_from."""
        if v and 'effective_from' in values and v <= values['effective_from']:
            raise ValueError('effective_to must be after effective_from')
        return v


class OverheadSettingsCreate(OverheadSettingsBase):
    """Schema for creating overhead settings."""
    pass


class OverheadSettingsUpdate(BaseModel):
    """Schema for updating overhead settings."""
    description: Optional[str] = Field(None, max_length=255)
    overhead_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    profit_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    safety_buffer_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    effective_to: Optional[date] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class OverheadSettingsResponse(OverheadSettingsBase):
    """Schema for overhead settings responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


class VehicleRateBase(BaseModel):
    """Base schema for vehicle rates."""
    vehicle_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    rate_per_mile: Decimal = Field(..., ge=0, decimal_places=3)
    driver_hourly_rate: Decimal = Field(..., ge=0, decimal_places=2)
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('effective_to')
    def validate_effective_to(cls, v, values):
        """Ensure effective_to is after effective_from."""
        if v and 'effective_from' in values and v <= values['effective_from']:
            raise ValueError('effective_to must be after effective_from')
        return v


class VehicleRateCreate(VehicleRateBase):
    """Schema for creating vehicle rate."""
    pass


class VehicleRateUpdate(BaseModel):
    """Schema for updating vehicle rate."""
    vehicle_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    rate_per_mile: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('rate_per_mile', pre=True)
    def quantize_rate(cls, v):
        """Ensure proper decimal precision."""
        if v is not None:
            return Decimal(str(v)).quantize(Decimal('0.01'))
        return v


class VehicleRateResponse(VehicleRateBase):
    """Schema for vehicle rate responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


class CostSummary(BaseModel):
    """Schema for cost summary at a specific date."""
    effective_date: date
    labor_rates: List[LaborRateResponse]
    equipment_costs: List[EquipmentCostResponse]
    overhead_settings: OverheadSettingsResponse
    vehicle_rates: List[VehicleRateResponse]
    
    class Config:
        from_attributes = True


class EffectiveDateQuery(BaseModel):
    """Schema for querying costs at a specific date."""
    effective_date: date = Field(default_factory=date.today)
    include_inactive: bool = False


# Disposal Fee Schemas
class DisposalFeeBase(BaseModel):
    """Base schema for disposal fees."""
    fee_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    fee_amount: Decimal = Field(..., ge=0, decimal_places=2)
    unit: str = Field(default="per_load", max_length=50)
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('fee_amount', pre=True)
    def quantize_fee(cls, v):
        """Ensure proper decimal precision."""
        return Decimal(str(v)).quantize(Decimal('0.01'))


class DisposalFeeCreate(DisposalFeeBase):
    """Schema for creating disposal fee."""
    pass


class DisposalFeeUpdate(BaseModel):
    """Schema for updating disposal fee."""
    fee_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    fee_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    unit: Optional[str] = Field(None, max_length=50)
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('fee_amount', pre=True)
    def quantize_fee(cls, v):
        """Ensure proper decimal precision."""
        if v is not None:
            return Decimal(str(v)).quantize(Decimal('0.01'))
        return v


class DisposalFeeResponse(DisposalFeeBase):
    """Schema for disposal fee responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


# Seasonal Adjustment Schemas
class SeasonalAdjustmentBase(BaseModel):
    """Base schema for seasonal adjustments."""
    season_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    adjustment_percent: Decimal = Field(..., decimal_places=2)
    start_month: int = Field(..., ge=1, le=12)
    start_day: int = Field(..., ge=1, le=31)
    end_month: int = Field(..., ge=1, le=12)
    end_day: int = Field(..., ge=1, le=31)
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('adjustment_percent', pre=True)
    def quantize_percent(cls, v):
        """Ensure proper decimal precision."""
        return Decimal(str(v)).quantize(Decimal('0.01'))


class SeasonalAdjustmentCreate(SeasonalAdjustmentBase):
    """Schema for creating seasonal adjustment."""
    pass


class SeasonalAdjustmentUpdate(BaseModel):
    """Schema for updating seasonal adjustment."""
    season_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    adjustment_percent: Optional[Decimal] = Field(None, decimal_places=2)
    start_month: Optional[int] = Field(None, ge=1, le=12)
    start_day: Optional[int] = Field(None, ge=1, le=31)
    end_month: Optional[int] = Field(None, ge=1, le=12)
    end_day: Optional[int] = Field(None, ge=1, le=31)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('adjustment_percent', pre=True)
    def quantize_percent(cls, v):
        """Ensure proper decimal precision."""
        if v is not None:
            return Decimal(str(v)).quantize(Decimal('0.01'))
        return v


class SeasonalAdjustmentResponse(SeasonalAdjustmentBase):
    """Schema for seasonal adjustment responses."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    updated_by: Optional[str]
    
    class Config:
        from_attributes = True


# Effective Costs Response
class EffectiveCostsResponse(BaseModel):
    """Response containing all effective costs for a given date."""
    effective_date: date
    labor_rates: List[LaborRateResponse]
    equipment_costs: List[EquipmentCostResponse]
    overhead_settings: Optional[OverheadSettingsResponse]
    vehicle_rates: List[VehicleRateResponse]
    disposal_fees: List[DisposalFeeResponse]
    seasonal_adjustments: List[SeasonalAdjustmentResponse]