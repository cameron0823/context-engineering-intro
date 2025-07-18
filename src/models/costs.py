"""
Cost management models with effective dating for temporal versioning.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, String, Date, Numeric, Boolean, Integer, 
    CheckConstraint, Index, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from src.models.base import BaseModel


class LaborRate(BaseModel):
    """Labor rates with effective dating for different roles."""
    __tablename__ = "labor_rates"
    
    # Role information
    role = Column(String(100), nullable=False)  # e.g., "climber", "groundsman", "crew_lead"
    description = Column(String(255), nullable=True)
    
    # Rate information (using Numeric for precise decimal handling)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    overtime_multiplier = Column(Numeric(3, 2), default=Decimal("1.5"))
    weekend_multiplier = Column(Numeric(3, 2), default=Decimal("2.0"))
    emergency_multiplier = Column(Numeric(3, 2), default=Decimal("2.5"))
    
    # Effective dating
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True, index=True)
    
    # Additional fields
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from', 
                       name='check_labor_rate_dates'),
        CheckConstraint('hourly_rate > 0', name='check_positive_hourly_rate'),
        CheckConstraint('overtime_multiplier >= 1', name='check_overtime_multiplier'),
        Index('idx_labor_rate_effective', 'role', 'effective_from', 'effective_to'),
        Index('idx_labor_rate_active', 'is_active', 'effective_from'),
    )
    
    @validates('effective_from', 'effective_to')
    def validate_dates(self, key, value):
        """Validate effective dates."""
        if key == 'effective_to' and value:
            if hasattr(self, 'effective_from') and self.effective_from and value <= self.effective_from:
                raise ValueError("effective_to must be after effective_from")
        return value
    
    @hybrid_property
    def is_current(self) -> bool:
        """Check if this rate is currently effective."""
        today = date.today()
        return (
            self.effective_from <= today and 
            (self.effective_to is None or self.effective_to > today)
        )
    
    def get_rate_for_conditions(
        self, 
        overtime: bool = False,
        weekend: bool = False,
        emergency: bool = False
    ) -> Decimal:
        """
        Calculate rate based on conditions.
        
        Args:
            overtime: Whether overtime rate applies
            weekend: Whether weekend rate applies
            emergency: Whether emergency rate applies
            
        Returns:
            Calculated hourly rate
        """
        rate = self.hourly_rate
        
        # Apply multipliers (use highest applicable)
        if emergency:
            rate *= self.emergency_multiplier
        elif weekend:
            rate *= self.weekend_multiplier
        elif overtime:
            rate *= self.overtime_multiplier
            
        return rate


class EquipmentCost(BaseModel):
    """Equipment costs with availability tracking."""
    __tablename__ = "equipment_costs"
    
    # Equipment information
    equipment_name = Column(String(100), nullable=False)
    equipment_type = Column(String(50), nullable=False)  # e.g., "vehicle", "chipper", "saw"
    model = Column(String(100), nullable=True)
    
    # Cost information
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    daily_rate = Column(Numeric(10, 2), nullable=True)
    fuel_cost_per_hour = Column(Numeric(10, 2), default=Decimal("0.00"))
    maintenance_cost_per_hour = Column(Numeric(10, 2), default=Decimal("0.00"))
    
    # Availability
    is_available = Column(Boolean, default=True, nullable=False)
    maintenance_due_date = Column(Date, nullable=True)
    
    # Effective dating
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True, index=True)
    
    # Additional fields
    notes = Column(String(500), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from', 
                       name='check_equipment_dates'),
        CheckConstraint('hourly_rate > 0', name='check_positive_equipment_rate'),
        Index('idx_equipment_effective', 'equipment_name', 'effective_from', 'effective_to'),
        Index('idx_equipment_available', 'is_available', 'effective_from'),
    )
    
    @hybrid_property
    def total_hourly_cost(self) -> Decimal:
        """Calculate total hourly cost including fuel and maintenance."""
        return self.hourly_rate + self.fuel_cost_per_hour + self.maintenance_cost_per_hour
    
    @hybrid_property
    def needs_maintenance(self) -> bool:
        """Check if equipment needs maintenance."""
        if not self.maintenance_due_date:
            return False
        return date.today() >= self.maintenance_due_date


class OverheadSettings(BaseModel):
    """Company overhead and margin settings with effective dating."""
    __tablename__ = "overhead_settings"
    
    # Setting name (for different scenarios)
    setting_name = Column(String(100), nullable=False)  # e.g., "standard", "government", "commercial"
    description = Column(String(255), nullable=True)
    
    # Percentages (stored as decimals, e.g., 25.5 for 25.5%)
    overhead_percent = Column(Numeric(5, 2), nullable=False)
    profit_percent = Column(Numeric(5, 2), nullable=False)
    safety_buffer_percent = Column(Numeric(5, 2), default=Decimal("10.0"))
    
    # Effective dating
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True, index=True)
    
    # Additional settings
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from', 
                       name='check_overhead_dates'),
        CheckConstraint('overhead_percent >= 0 AND overhead_percent <= 100', 
                       name='check_overhead_percent'),
        CheckConstraint('profit_percent >= 0 AND profit_percent <= 100', 
                       name='check_profit_percent'),
        CheckConstraint('safety_buffer_percent >= 0 AND safety_buffer_percent <= 100', 
                       name='check_safety_buffer_percent'),
        Index('idx_overhead_effective', 'setting_name', 'effective_from', 'effective_to'),
        Index('idx_overhead_default', 'is_default', 'effective_from'),
    )


class VehicleRate(BaseModel):
    """Vehicle mileage rates with effective dating."""
    __tablename__ = "vehicle_rates"
    
    # Vehicle information
    vehicle_type = Column(String(50), nullable=False)  # e.g., "truck", "chipper_truck", "pickup"
    description = Column(String(255), nullable=True)
    
    # Rate information
    rate_per_mile = Column(Numeric(10, 3), nullable=False)
    driver_hourly_rate = Column(Numeric(10, 2), nullable=False)
    
    # Effective dating
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True, index=True)
    
    # Additional fields
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from', 
                       name='check_vehicle_dates'),
        CheckConstraint('rate_per_mile > 0', name='check_positive_vehicle_rate'),
        CheckConstraint('driver_hourly_rate > 0', name='check_positive_driver_rate'),
        Index('idx_vehicle_effective', 'vehicle_type', 'effective_from', 'effective_to'),
    )


class DisposalFee(BaseModel):
    """Disposal fees for different materials."""
    __tablename__ = "disposal_fees"
    
    # Material information
    material_type = Column(String(100), nullable=False)  # e.g., "green_waste", "wood_chips", "logs"
    description = Column(String(255), nullable=True)
    
    # Fee information
    fee_per_ton = Column(Numeric(10, 2), nullable=False)
    fee_per_cubic_yard = Column(Numeric(10, 2), nullable=True)
    minimum_fee = Column(Numeric(10, 2), default=Decimal("0.00"))
    
    # Location-specific
    disposal_site = Column(String(255), nullable=True)
    distance_miles = Column(Numeric(10, 1), nullable=True)
    
    # Effective dating
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True, index=True)
    
    # Additional fields
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from', 
                       name='check_disposal_dates'),
        CheckConstraint('fee_per_ton >= 0', name='check_non_negative_disposal_fee'),
        Index('idx_disposal_effective', 'material_type', 'effective_from', 'effective_to'),
    )


class SeasonalAdjustment(BaseModel):
    """Seasonal cost adjustments."""
    __tablename__ = "seasonal_adjustments"
    
    # Season information
    season_name = Column(String(50), nullable=False)  # e.g., "winter", "summer", "storm_season"
    description = Column(String(255), nullable=True)
    
    # Date range (recurring yearly)
    start_month = Column(Integer, nullable=False)  # 1-12
    start_day = Column(Integer, nullable=False)    # 1-31
    end_month = Column(Integer, nullable=False)    # 1-12
    end_day = Column(Integer, nullable=False)      # 1-31
    
    # Adjustment percentages
    labor_adjustment_percent = Column(Numeric(5, 2), default=Decimal("0.00"))
    equipment_adjustment_percent = Column(Numeric(5, 2), default=Decimal("0.00"))
    
    # Effective dating for the adjustment rule itself
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date, nullable=True, index=True)
    
    # Additional fields
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('effective_to IS NULL OR effective_to > effective_from', 
                       name='check_seasonal_dates'),
        CheckConstraint('start_month >= 1 AND start_month <= 12', name='check_start_month'),
        CheckConstraint('end_month >= 1 AND end_month <= 12', name='check_end_month'),
        CheckConstraint('start_day >= 1 AND start_day <= 31', name='check_start_day'),
        CheckConstraint('end_day >= 1 AND end_day <= 31', name='check_end_day'),
        Index('idx_seasonal_effective', 'season_name', 'effective_from', 'effective_to'),
    )
    
    def is_date_in_season(self, check_date: date) -> bool:
        """
        Check if a date falls within this seasonal adjustment period.
        
        Args:
            check_date: Date to check
            
        Returns:
            True if date is in season, False otherwise
        """
        # Check if adjustment is active
        if not self.is_active:
            return False
            
        # Check effective dating
        if check_date < self.effective_from:
            return False
        if self.effective_to and check_date >= self.effective_to:
            return False
        
        # Create date ranges for comparison
        check_month_day = (check_date.month, check_date.day)
        start_month_day = (self.start_month, self.start_day)
        end_month_day = (self.end_month, self.end_day)
        
        # Handle year-crossing seasons (e.g., winter)
        if start_month_day <= end_month_day:
            # Season within same year
            return start_month_day <= check_month_day <= end_month_day
        else:
            # Season crosses year boundary
            return check_month_day >= start_month_day or check_month_day <= end_month_day