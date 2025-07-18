"""
Calculation service layer that orchestrates cost calculations.
"""
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import structlog

from src.models.costs import (
    LaborRate, EquipmentCost, OverheadSettings,
    VehicleRate, DisposalFee, SeasonalAdjustment
)
from src.schemas.calculation import CalculationInput, CalculationResult
from src.core.calculator import TreeServiceCalculator
from src.core.config import settings
from src.services.external_apis import get_external_api_service, GoogleMapsError


logger = structlog.get_logger()


class CalculationService:
    """
    Service layer for orchestrating calculations with current cost data.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.calculator = TreeServiceCalculator()
    
    async def calculate_estimate(
        self,
        calculation_input: CalculationInput,
        calculation_date: Optional[date] = None,
        use_google_maps: bool = False,
        origin_address: Optional[str] = None,
        destination_address: Optional[str] = None
    ) -> CalculationResult:
        """
        Calculate an estimate using current or historical cost data.
        
        Args:
            calculation_input: The calculation input data
            calculation_date: Date for historical calculations (default: today)
            use_google_maps: Whether to use Google Maps for distance calculation
            origin_address: Origin address for Google Maps calculation
            destination_address: Destination address for Google Maps calculation
            
        Returns:
            CalculationResult with all cost breakdowns
        """
        if not calculation_date:
            calculation_date = date.today()
        
        # If Google Maps is requested and addresses provided, calculate actual distance
        if use_google_maps and origin_address and destination_address:
            try:
                api_service = get_external_api_service()
                travel_distance = await api_service.calculate_travel_distance(
                    origin=origin_address,
                    destination=destination_address
                )
                # Update the calculation input with actual distance
                calculation_input.travel_details.miles = Decimal(str(travel_distance.distance_miles))
                logger.info(
                    "Used Google Maps for distance calculation",
                    miles=travel_distance.distance_miles,
                    duration_minutes=travel_distance.duration_minutes
                )
            except GoogleMapsError as e:
                logger.warning(
                    "Failed to calculate distance with Google Maps, using provided value",
                    error=str(e)
                )
        
        # Validate and enrich input with current costs
        enriched_input = await self._enrich_calculation_input(
            calculation_input,
            calculation_date
        )
        
        # Perform calculation
        result = self.calculator.calculate_estimate(enriched_input)
        
        # Apply seasonal adjustments if any
        seasonal_adjustment = await self._get_seasonal_adjustment(calculation_date)
        if seasonal_adjustment:
            result = self._apply_seasonal_adjustment(result, seasonal_adjustment)
        
        return result
    
    async def _enrich_calculation_input(
        self,
        calculation_input: CalculationInput,
        calculation_date: date
    ) -> CalculationInput:
        """
        Enrich calculation input with current cost data from database.
        """
        # Get current rates
        labor_rates = await self._get_labor_rates(calculation_date)
        equipment_costs = await self._get_equipment_costs()
        overhead_settings = await self._get_overhead_settings(calculation_date)
        vehicle_rates = await self._get_vehicle_rates(calculation_date)
        
        # Update crew hourly rates from database
        for crew_member in calculation_input.labor_details.crew:
            rate = labor_rates.get(crew_member.role)
            if rate:
                crew_member.hourly_rate = rate.hourly_rate
        
        # Update equipment hourly costs from database
        if calculation_input.equipment_details:
            equipment_map = {eq.id: eq for eq in equipment_costs}
            for equipment in calculation_input.equipment_details:
                eq_data = equipment_map.get(equipment.equipment_id)
                if eq_data:
                    equipment.hourly_cost = eq_data.hourly_cost
        
        # Update overhead settings
        if overhead_settings:
            calculation_input.margins.overhead_percent = overhead_settings.base_overhead_percent
            
            # Apply large job discount if applicable
            if calculation_input.labor_details.estimated_hours > overhead_settings.large_job_threshold:
                discount = overhead_settings.large_job_discount_percent
                calculation_input.margins.overhead_percent -= discount
            
            # Apply small job premium if applicable
            elif calculation_input.labor_details.estimated_hours < overhead_settings.small_job_threshold:
                premium = overhead_settings.small_job_premium_percent
                calculation_input.margins.overhead_percent += premium
        
        # Update vehicle rates
        if vehicle_rates:
            # Use the first active vehicle rate (could be enhanced to select specific vehicle type)
            vehicle_rate = vehicle_rates[0]
            calculation_input.travel_details.vehicle_rate_per_mile = vehicle_rate.rate_per_mile
            calculation_input.travel_details.driver_hourly_rate = vehicle_rate.driver_hourly_rate
        
        return calculation_input
    
    async def _get_labor_rates(self, effective_date: date) -> Dict[str, LaborRate]:
        """Get labor rates effective on the given date."""
        query = select(LaborRate).where(
            and_(
                LaborRate.deleted_at.is_(None),
                LaborRate.effective_from <= effective_date,
                or_(
                    LaborRate.effective_to.is_(None),
                    LaborRate.effective_to >= effective_date
                )
            )
        )
        
        result = await self.db.execute(query)
        rates = result.scalars().all()
        
        return {rate.role: rate for rate in rates}
    
    async def _get_equipment_costs(self) -> List[EquipmentCost]:
        """Get available equipment costs."""
        query = select(EquipmentCost).where(
            and_(
                EquipmentCost.deleted_at.is_(None),
                EquipmentCost.available == True
            )
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _get_overhead_settings(self, effective_date: date) -> Optional[OverheadSettings]:
        """Get overhead settings effective on the given date."""
        query = select(OverheadSettings).where(
            and_(
                OverheadSettings.deleted_at.is_(None),
                OverheadSettings.effective_from <= effective_date,
                or_(
                    OverheadSettings.effective_to.is_(None),
                    OverheadSettings.effective_to >= effective_date
                )
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_vehicle_rates(self, effective_date: date) -> List[VehicleRate]:
        """Get vehicle rates effective on the given date."""
        query = select(VehicleRate).where(
            and_(
                VehicleRate.deleted_at.is_(None),
                VehicleRate.effective_from <= effective_date,
                or_(
                    VehicleRate.effective_to.is_(None),
                    VehicleRate.effective_to >= effective_date
                )
            )
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _get_seasonal_adjustment(self, check_date: date) -> Optional[SeasonalAdjustment]:
        """Get active seasonal adjustment for the given date."""
        query = select(SeasonalAdjustment).where(
            and_(
                SeasonalAdjustment.deleted_at.is_(None),
                SeasonalAdjustment.active == True
            )
        )
        
        result = await self.db.execute(query)
        adjustments = result.scalars().all()
        
        # Check if date falls within any adjustment period
        month = check_date.month
        day = check_date.day
        
        for adj in adjustments:
            if adj.start_month <= adj.end_month:
                # Normal case: adjustment doesn't span year boundary
                if (month > adj.start_month or (month == adj.start_month and day >= adj.start_day)) and \
                   (month < adj.end_month or (month == adj.end_month and day <= adj.end_day)):
                    return adj
            else:
                # Adjustment spans year boundary (e.g., Dec to Feb)
                if (month > adj.start_month or (month == adj.start_month and day >= adj.start_day)) or \
                   (month < adj.end_month or (month == adj.end_month and day <= adj.end_day)):
                    return adj
        
        return None
    
    def _apply_seasonal_adjustment(
        self,
        result: CalculationResult,
        adjustment: SeasonalAdjustment
    ) -> CalculationResult:
        """Apply seasonal adjustment to the calculation result."""
        # Calculate adjustment amount on the subtotal (before final rounding)
        adjustment_amount = result.subtotal * (adjustment.adjustment_percent / Decimal('100'))
        adjustment_amount = adjustment_amount.quantize(Decimal('0.01'))
        
        # Update the result
        result.subtotal += adjustment_amount
        result.final_total = (result.subtotal / Decimal('5')).quantize(
            Decimal('1'), rounding=Decimal.ROUND_HALF_UP
        ) * Decimal('5')
        
        # Add adjustment details to calculation details
        if 'seasonal_adjustment' not in result.calculation_details:
            result.calculation_details['seasonal_adjustment'] = {
                'name': adjustment.name,
                'percent': str(adjustment.adjustment_percent),
                'amount': str(adjustment_amount)
            }
        
        return result
    
    async def validate_calculation_inputs(
        self,
        calculation_input: CalculationInput
    ) -> tuple[bool, Optional[str]]:
        """
        Validate calculation inputs against business rules and data availability.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check travel distance
        if calculation_input.travel_details.miles > settings.MAX_TRAVEL_MILES:
            return False, f"Travel distance exceeds maximum of {settings.MAX_TRAVEL_MILES} miles"
        
        # Check estimated hours
        if calculation_input.labor_details.estimated_hours > settings.MAX_ESTIMATE_HOURS:
            return False, f"Estimated hours exceeds maximum of {settings.MAX_ESTIMATE_HOURS} hours"
        
        # Check crew size
        crew_size = len(calculation_input.labor_details.crew)
        if crew_size > settings.MAX_CREW_SIZE:
            return False, f"Crew size {crew_size} exceeds maximum of {settings.MAX_CREW_SIZE}"
        
        # Validate labor roles exist
        labor_rates = await self._get_labor_rates(date.today())
        for crew_member in calculation_input.labor_details.crew:
            if crew_member.role not in labor_rates:
                return False, f"No labor rate found for role: {crew_member.role}"
        
        # Validate equipment exists and is available
        if calculation_input.equipment_details:
            equipment_costs = await self._get_equipment_costs()
            equipment_ids = {eq.id for eq in equipment_costs}
            
            for equipment in calculation_input.equipment_details:
                if equipment.equipment_id not in equipment_ids:
                    return False, f"Equipment ID {equipment.equipment_id} not found or unavailable"
        
        # Check overhead settings exist
        overhead_settings = await self._get_overhead_settings(date.today())
        if not overhead_settings:
            return False, "No overhead settings configured for current date"
        
        # Check vehicle rates exist
        vehicle_rates = await self._get_vehicle_rates(date.today())
        if not vehicle_rates:
            return False, "No vehicle rates configured for current date"
        
        return True, None
    
    async def get_available_roles(self) -> List[str]:
        """Get list of roles with active labor rates."""
        query = select(LaborRate.role).distinct().where(
            and_(
                LaborRate.deleted_at.is_(None),
                LaborRate.effective_from <= date.today(),
                or_(
                    LaborRate.effective_to.is_(None),
                    LaborRate.effective_to >= date.today()
                )
            )
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_available_equipment(self) -> List[Dict[str, Any]]:
        """Get list of available equipment with details."""
        equipment_list = await self._get_equipment_costs()
        
        return [
            {
                "id": eq.id,
                "name": eq.name,
                "type": eq.type,
                "hourly_cost": str(eq.hourly_cost),
                "daily_cost": str(eq.daily_cost) if eq.daily_cost else None,
                "setup_cost": str(eq.setup_cost) if eq.setup_cost else None
            }
            for eq in equipment_list
        ]