"""
Deterministic calculator engine for tree service estimates.
All calculations use Decimal for precision and produce consistent results.
"""
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import uuid
import hashlib
import json

from src.core.config import settings


# Set decimal precision for financial calculations
getcontext().prec = 10


class DeterministicCalculator:
    """
    Pure functional calculator with deterministic output.
    All methods are static to ensure no hidden state affects calculations.
    """
    
    @staticmethod
    def round_to_cents(value: Decimal) -> Decimal:
        """Round a decimal value to 2 decimal places (cents)."""
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def round_to_nearest_five(value: Decimal) -> Decimal:
        """Round a decimal value to the nearest $5."""
        return (value / Decimal('5')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('5')
    
    @staticmethod
    def calculate_travel_cost(
        miles: Decimal,
        time_minutes: int,
        vehicle_rate_per_mile: Decimal,
        driver_hourly_rate: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate travel costs based on mileage and time.
        
        Args:
            miles: Distance in miles
            time_minutes: Travel time in minutes
            vehicle_rate_per_mile: Cost per mile for vehicle
            driver_hourly_rate: Driver's hourly rate
            
        Returns:
            Dictionary with mileage_cost, time_cost, and total
        """
        # Ensure all inputs are Decimal
        miles = Decimal(str(miles))
        vehicle_rate_per_mile = Decimal(str(vehicle_rate_per_mile))
        driver_hourly_rate = Decimal(str(driver_hourly_rate))
        
        # Calculate mileage cost
        mileage_cost = miles * vehicle_rate_per_mile
        
        # Calculate time cost (convert minutes to hours)
        time_hours = Decimal(str(time_minutes)) / Decimal('60')
        time_cost = time_hours * driver_hourly_rate
        
        # Round to cents
        mileage_cost = DeterministicCalculator.round_to_cents(mileage_cost)
        time_cost = DeterministicCalculator.round_to_cents(time_cost)
        total = DeterministicCalculator.round_to_cents(mileage_cost + time_cost)
        
        return {
            "mileage_cost": mileage_cost,
            "time_cost": time_cost,
            "total": total
        }
    
    @staticmethod
    def calculate_labor_cost(
        hours: Decimal,
        crew: List[Dict[str, Decimal]],
        multipliers: Dict[str, Decimal]
    ) -> Dict[str, any]:
        """
        Calculate labor costs for the crew.
        
        Args:
            hours: Number of hours worked
            crew: List of crew members with hourly_rate
            multipliers: Dictionary of multipliers to apply (sorted by key)
            
        Returns:
            Dictionary with base_cost, multipliers_applied, and total
        """
        # Ensure hours is Decimal
        hours = Decimal(str(hours))
        
        # Calculate base cost
        base_cost = Decimal('0')
        for worker in crew:
            hourly_rate = Decimal(str(worker['hourly_rate']))
            base_cost += hours * hourly_rate
        
        # Apply multipliers in deterministic order (sorted by key)
        total = base_cost
        applied_multipliers = {}
        for key in sorted(multipliers.keys()):
            multiplier = Decimal(str(multipliers[key]))
            total *= multiplier
            applied_multipliers[key] = str(multiplier)
        
        # Round to cents
        base_cost = DeterministicCalculator.round_to_cents(base_cost)
        total = DeterministicCalculator.round_to_cents(total)
        
        return {
            "base_cost": base_cost,
            "multipliers_applied": applied_multipliers,
            "total": total
        }
    
    @staticmethod
    def calculate_equipment_cost(
        hours: Decimal,
        equipment_list: List[Dict[str, Decimal]]
    ) -> Dict[str, Decimal]:
        """
        Calculate equipment costs.
        
        Args:
            hours: Number of hours equipment is used
            equipment_list: List of equipment with hourly costs
            
        Returns:
            Dictionary with itemized costs and total
        """
        # Ensure hours is Decimal
        hours = Decimal(str(hours))
        
        total = Decimal('0')
        itemized = {}
        
        # Sort equipment by ID for deterministic order
        sorted_equipment = sorted(equipment_list, key=lambda x: x.get('id', 0))
        
        for equipment in sorted_equipment:
            equipment_id = str(equipment.get('id', 'unknown'))
            hourly_cost = Decimal(str(equipment['hourly_cost']))
            cost = hours * hourly_cost
            cost = DeterministicCalculator.round_to_cents(cost)
            itemized[f"equipment_{equipment_id}"] = cost
            total += cost
        
        return {
            "itemized": itemized,
            "total": DeterministicCalculator.round_to_cents(total)
        }
    
    @staticmethod
    def apply_formula_pipeline(
        components: Dict[str, Decimal],
        overhead_percent: Decimal,
        profit_percent: Decimal,
        safety_buffer_percent: Decimal
    ) -> Dict[str, any]:
        """
        Apply the deterministic formula pipeline to calculate final estimate.
        
        Formula order:
        1. Sum all direct costs
        2. Apply overhead
        3. Apply safety buffer
        4. Apply profit margin
        5. Round to nearest $5
        
        Args:
            components: Dictionary of cost components
            overhead_percent: Overhead percentage (e.g., 25.0 for 25%)
            profit_percent: Profit margin percentage
            safety_buffer_percent: Safety buffer percentage
            
        Returns:
            Dictionary with all calculation steps and final total
        """
        # Ensure all percentages are Decimal
        overhead_percent = Decimal(str(overhead_percent))
        profit_percent = Decimal(str(profit_percent))
        safety_buffer_percent = Decimal(str(safety_buffer_percent))
        
        # Step 1: Sum all direct costs (in sorted order for determinism)
        direct_costs = Decimal('0')
        for key in sorted(components.keys()):
            direct_costs += Decimal(str(components[key]))
        direct_costs = DeterministicCalculator.round_to_cents(direct_costs)
        
        # Step 2: Apply overhead
        overhead = direct_costs * (overhead_percent / Decimal('100'))
        overhead = DeterministicCalculator.round_to_cents(overhead)
        subtotal_with_overhead = direct_costs + overhead
        
        # Step 3: Apply safety buffer
        safety_buffer = subtotal_with_overhead * (safety_buffer_percent / Decimal('100'))
        safety_buffer = DeterministicCalculator.round_to_cents(safety_buffer)
        subtotal_with_buffer = subtotal_with_overhead + safety_buffer
        
        # Step 4: Apply profit margin
        profit = subtotal_with_buffer * (profit_percent / Decimal('100'))
        profit = DeterministicCalculator.round_to_cents(profit)
        final_subtotal = subtotal_with_buffer + profit
        
        # Step 5: Round to nearest $5
        final_total = DeterministicCalculator.round_to_nearest_five(final_subtotal)
        
        # Generate calculation ID and timestamp
        calculation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        return {
            "direct_costs": direct_costs,
            "overhead": overhead,
            "overhead_percent": str(overhead_percent),
            "safety_buffer": safety_buffer,
            "safety_buffer_percent": str(safety_buffer_percent),
            "profit": profit,
            "profit_percent": str(profit_percent),
            "subtotal": final_subtotal,
            "final_total": final_total,
            "calculation_id": calculation_id,
            "timestamp": timestamp.isoformat(),
            "formula_version": "1.0"
        }
    
    @staticmethod
    def calculate_full_estimate(
        travel_miles: Decimal,
        travel_time_minutes: int,
        estimated_hours: Decimal,
        crew_rates: List[Dict[str, Decimal]],
        equipment_list: List[Dict[str, Decimal]],
        vehicle_rate_per_mile: Decimal,
        driver_hourly_rate: Decimal,
        disposal_fees: Decimal,
        permit_cost: Decimal,
        overhead_percent: Decimal,
        profit_percent: Decimal,
        safety_buffer_percent: Decimal,
        emergency_job: bool = False,
        weekend_work: bool = False
    ) -> Dict[str, any]:
        """
        Calculate a complete estimate with all components.
        
        This is the main entry point that orchestrates all calculations.
        
        Returns:
            Complete calculation breakdown with final total
        """
        # Calculate travel costs
        travel_costs = DeterministicCalculator.calculate_travel_cost(
            miles=travel_miles,
            time_minutes=travel_time_minutes,
            vehicle_rate_per_mile=vehicle_rate_per_mile,
            driver_hourly_rate=driver_hourly_rate
        )
        
        # Determine labor multipliers
        multipliers = {}
        if emergency_job:
            multipliers["emergency"] = Decimal("2.5")
        elif weekend_work:
            multipliers["weekend"] = Decimal("2.0")
        
        # Calculate labor costs
        labor_costs = DeterministicCalculator.calculate_labor_cost(
            hours=estimated_hours,
            crew=crew_rates,
            multipliers=multipliers
        )
        
        # Calculate equipment costs
        equipment_costs = DeterministicCalculator.calculate_equipment_cost(
            hours=estimated_hours,
            equipment_list=equipment_list
        )
        
        # Ensure other costs are Decimal
        disposal_fees = Decimal(str(disposal_fees))
        permit_cost = Decimal(str(permit_cost))
        
        # Combine all cost components
        components = {
            "travel": travel_costs["total"],
            "labor": labor_costs["total"],
            "equipment": equipment_costs["total"],
            "disposal": disposal_fees,
            "permits": permit_cost
        }
        
        # Apply formula pipeline
        final_calculation = DeterministicCalculator.apply_formula_pipeline(
            components=components,
            overhead_percent=overhead_percent,
            profit_percent=profit_percent,
            safety_buffer_percent=safety_buffer_percent
        )
        
        # Create comprehensive result
        return {
            "travel_breakdown": travel_costs,
            "labor_breakdown": labor_costs,
            "equipment_breakdown": equipment_costs,
            "disposal_fees": disposal_fees,
            "permit_cost": permit_cost,
            "cost_components": components,
            "final_calculation": final_calculation,
            "calculation_checksum": DeterministicCalculator.generate_checksum(final_calculation)
        }
    
    @staticmethod
    def generate_checksum(calculation_result: Dict) -> str:
        """
        Generate a checksum for the calculation to verify consistency.
        
        Args:
            calculation_result: The calculation result dictionary
            
        Returns:
            SHA-256 checksum of the calculation
        """
        # Create a deterministic string representation
        # Sort keys to ensure consistent ordering
        checksum_data = {
            "direct_costs": str(calculation_result.get("direct_costs", 0)),
            "overhead": str(calculation_result.get("overhead", 0)),
            "safety_buffer": str(calculation_result.get("safety_buffer", 0)),
            "profit": str(calculation_result.get("profit", 0)),
            "final_total": str(calculation_result.get("final_total", 0)),
            "formula_version": calculation_result.get("formula_version", "1.0")
        }
        
        # Create JSON string with sorted keys
        json_str = json.dumps(checksum_data, sort_keys=True)
        
        # Generate SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    @staticmethod
    def validate_calculation_inputs(
        travel_miles: Decimal,
        estimated_hours: Decimal,
        crew_size: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate calculation inputs against business rules.
        
        Args:
            travel_miles: Distance to job site
            estimated_hours: Estimated work hours
            crew_size: Number of crew members
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check travel distance
        if travel_miles > settings.MAX_TRAVEL_MILES:
            return False, f"Travel distance {travel_miles} exceeds maximum of {settings.MAX_TRAVEL_MILES} miles"
        
        # Check estimated hours
        if estimated_hours > settings.MAX_ESTIMATE_HOURS:
            return False, f"Estimated hours {estimated_hours} exceeds maximum of {settings.MAX_ESTIMATE_HOURS} hours"
        
        # Check crew size
        if crew_size > settings.MAX_CREW_SIZE:
            return False, f"Crew size {crew_size} exceeds maximum of {settings.MAX_CREW_SIZE}"
        
        # Check minimum values
        if travel_miles < 0:
            return False, "Travel distance cannot be negative"
        
        if estimated_hours <= 0:
            return False, "Estimated hours must be greater than zero"
        
        if crew_size <= 0:
            return False, "Crew size must be at least 1"
        
        return True, None


class TreeServiceCalculator:
    """
    High-level calculator that integrates with schemas and provides
    a simpler interface for the API endpoints.
    """
    
    def __init__(self):
        self.calculator = DeterministicCalculator()
    
    def calculate_estimate(self, calculation_input) -> 'CalculationResult':
        """
        Calculate estimate from CalculationInput schema.
        
        Args:
            calculation_input: CalculationInput schema instance
            
        Returns:
            CalculationResult schema instance
        """
        from src.schemas.calculation import CalculationResult
        
        # Extract input values
        travel = calculation_input.travel_details
        labor = calculation_input.labor_details
        equipment = calculation_input.equipment_details or []
        margins = calculation_input.margins
        
        # Calculate full estimate
        result = self.calculator.calculate_full_estimate(
            travel_miles=travel.miles,
            travel_time_minutes=travel.estimated_minutes,
            estimated_hours=labor.estimated_hours,
            crew_rates=[{"hourly_rate": crew.hourly_rate} for crew in labor.crew],
            equipment_list=[
                {"id": eq.equipment_id, "hourly_cost": eq.hourly_cost}
                for eq in equipment
            ],
            vehicle_rate_per_mile=travel.vehicle_rate_per_mile,
            driver_hourly_rate=travel.driver_hourly_rate,
            disposal_fees=calculation_input.disposal_fees,
            permit_cost=calculation_input.permit_cost,
            overhead_percent=margins.overhead_percent,
            profit_percent=margins.profit_percent,
            safety_buffer_percent=margins.safety_buffer_percent,
            emergency_job=labor.emergency,
            weekend_work=labor.weekend
        )
        
        # Extract final calculation
        final_calc = result["final_calculation"]
        
        # Create and return CalculationResult
        return CalculationResult(
            calculation_id=final_calc["calculation_id"],
            travel_cost=result["travel_breakdown"]["total"],
            labor_cost=result["labor_breakdown"]["total"],
            equipment_cost=result["equipment_breakdown"]["total"],
            disposal_fees=result["disposal_fees"],
            permit_cost=result["permit_cost"],
            direct_costs=final_calc["direct_costs"],
            overhead_amount=final_calc["overhead"],
            safety_buffer_amount=final_calc["safety_buffer"],
            profit_amount=final_calc["profit"],
            subtotal=final_calc["subtotal"],
            final_total=final_calc["final_total"],
            checksum=result["calculation_checksum"],
            calculation_details={
                "travel_breakdown": result["travel_breakdown"],
                "labor_breakdown": result["labor_breakdown"],
                "equipment_breakdown": result["equipment_breakdown"],
                "cost_components": result["cost_components"],
                "margins_applied": {
                    "overhead_percent": final_calc["overhead_percent"],
                    "safety_buffer_percent": final_calc["safety_buffer_percent"],
                    "profit_percent": final_calc["profit_percent"]
                },
                "formula_version": final_calc["formula_version"],
                "timestamp": final_calc["timestamp"]
            }
        )
    
    def calculate_estimate_from_dict(self, calculation_dict: Dict) -> 'CalculationResult':
        """
        Calculate estimate from a dictionary (for duplicating estimates).
        
        Args:
            calculation_dict: Dictionary of calculation inputs
            
        Returns:
            CalculationResult schema instance
        """
        from src.schemas.calculation import CalculationInput
        
        # Convert dict to CalculationInput schema
        calculation_input = CalculationInput(**calculation_dict)
        
        # Use the main calculation method
        return self.calculate_estimate(calculation_input)