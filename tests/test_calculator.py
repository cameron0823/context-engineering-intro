"""
Tests for the tree service calculator.
"""
import pytest
from decimal import Decimal

from src.core.calculator import TreeServiceCalculator, EstimateCalculation


class TestCalculatorBasics:
    """Test basic calculator functionality."""
    
    def test_labor_cost_calculation(self):
        """Test labor cost calculation."""
        inputs = EstimateCalculation(
            travel_hours=Decimal("1.0"),
            setup_hours=Decimal("0.5"),
            work_hours=Decimal("4.0"),
            num_crew=3,
            crew_hourly_rate=Decimal("50.00")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Total hours = 1.0 + 0.5 + 4.0 = 5.5
        # Labor cost = 5.5 * 3 * 50 = 825
        assert result.labor_cost == Decimal("825.00")
    
    def test_equipment_cost_calculation(self):
        """Test equipment cost calculation."""
        inputs = EstimateCalculation(
            work_hours=Decimal("4.0"),
            num_crew=2,
            equipment_hours=Decimal("3.0"),
            equipment_list=["chipper", "stump_grinder"],
            chipper_rate=Decimal("75.00"),
            stump_grinder_rate=Decimal("100.00")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Equipment cost = 3.0 * (75 + 100) = 525
        assert result.equipment_cost == Decimal("525.00")
    
    def test_vehicle_cost_calculation(self):
        """Test vehicle cost calculation."""
        inputs = EstimateCalculation(
            work_hours=Decimal("4.0"),
            num_crew=2,
            travel_distance_miles=Decimal("25.0"),
            vehicle_rate_per_mile=Decimal("0.65"),
            driver_hourly_rate=Decimal("25.00")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Vehicle cost = (25 * 2 * 0.65) + (2 * 25) = 32.50 + 50 = 82.50
        assert result.vehicle_cost == Decimal("82.50")
    
    def test_disposal_cost_calculation(self):
        """Test disposal cost calculation."""
        inputs = EstimateCalculation(
            work_hours=Decimal("4.0"),
            num_crew=2,
            disposal_trips=2,
            disposal_fee_per_trip=Decimal("50.00"),
            material_disposal_tons=Decimal("2.5"),
            disposal_fee_per_ton=Decimal("40.00")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Disposal cost = (2 * 50) + (2.5 * 40) = 100 + 100 = 200
        assert result.disposal_cost == Decimal("200.00")
    
    def test_overhead_and_profit_calculation(self):
        """Test overhead and profit calculation."""
        inputs = EstimateCalculation(
            work_hours=Decimal("4.0"),
            num_crew=2,
            crew_hourly_rate=Decimal("50.00"),
            overhead_percent=Decimal("25.0"),
            profit_percent=Decimal("35.0")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Labor cost = 4 * 2 * 50 = 400
        # Subtotal = 400
        # Overhead = 400 * 0.25 = 100
        # Total cost = 400 + 100 = 500
        # Profit = 500 * 0.35 = 175
        # Total price = 500 + 175 = 675
        assert result.labor_cost == Decimal("400.00")
        assert result.subtotal == Decimal("400.00")
        assert result.overhead_amount == Decimal("100.00")
        assert result.total_cost == Decimal("500.00")
        assert result.profit_amount == Decimal("175.00")
        assert result.total_price == Decimal("675.00")
    
    def test_safety_buffer_calculation(self):
        """Test safety buffer calculation."""
        inputs = EstimateCalculation(
            work_hours=Decimal("4.0"),
            num_crew=2,
            crew_hourly_rate=Decimal("50.00"),
            overhead_percent=Decimal("25.0"),
            safety_buffer_percent=Decimal("10.0"),
            profit_percent=Decimal("35.0")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Labor cost = 400
        # Subtotal = 400
        # Overhead = 100
        # Safety buffer = 400 * 0.10 = 40
        # Total cost = 400 + 100 + 40 = 540
        # Profit = 540 * 0.35 = 189
        # Total price = 540 + 189 = 729
        assert result.safety_buffer_amount == Decimal("40.00")
        assert result.total_cost == Decimal("540.00")
        assert result.profit_amount == Decimal("189.00")
        assert result.total_price == Decimal("729.00")
    
    def test_rounding_to_nearest_five(self):
        """Test that total price is rounded to nearest $5."""
        inputs = EstimateCalculation(
            work_hours=Decimal("3.75"),
            num_crew=2,
            crew_hourly_rate=Decimal("47.50"),
            overhead_percent=Decimal("25.0"),
            profit_percent=Decimal("35.0")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Total price should be rounded to nearest $5
        assert result.total_price % 5 == 0


class TestCalculatorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_hours(self):
        """Test calculation with zero hours."""
        inputs = EstimateCalculation(
            work_hours=Decimal("0.0"),
            num_crew=2
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        assert result.labor_cost == Decimal("0.00")
        assert result.total_price == Decimal("0.00")
    
    def test_zero_crew(self):
        """Test calculation with zero crew members."""
        inputs = EstimateCalculation(
            work_hours=Decimal("4.0"),
            num_crew=0
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        assert result.labor_cost == Decimal("0.00")
    
    def test_negative_values(self):
        """Test that negative values are handled."""
        with pytest.raises(ValueError):
            inputs = EstimateCalculation(
                work_hours=Decimal("-4.0"),
                num_crew=2
            )
    
    def test_very_large_values(self):
        """Test calculation with very large values."""
        inputs = EstimateCalculation(
            work_hours=Decimal("100.0"),
            num_crew=10,
            crew_hourly_rate=Decimal("100.00"),
            equipment_hours=Decimal("100.0"),
            equipment_list=["chipper", "bucket_truck", "stump_grinder"],
            chipper_rate=Decimal("100.00"),
            bucket_truck_rate=Decimal("200.00"),
            stump_grinder_rate=Decimal("150.00")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Ensure calculations don't overflow
        assert result.total_price > Decimal("0")
        assert result.total_price < Decimal("1000000")  # Reasonable upper bound


class TestCalculatorWithCosts:
    """Test calculator with actual cost data."""
    
    def test_with_overtime_multiplier(self):
        """Test calculation with overtime rates."""
        inputs = EstimateCalculation(
            work_hours=Decimal("10.0"),  # Long day = overtime
            num_crew=3,
            crew_hourly_rate=Decimal("50.00"),
            overtime_multiplier=Decimal("1.5"),
            overtime_threshold_hours=8
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # First 8 hours: 8 * 3 * 50 = 1200
        # Overtime 2 hours: 2 * 3 * 50 * 1.5 = 450
        # Total: 1200 + 450 = 1650
        expected_labor = Decimal("1650.00")
        assert result.labor_cost == expected_labor
    
    def test_with_weekend_multiplier(self):
        """Test calculation with weekend rates."""
        inputs = EstimateCalculation(
            work_hours=Decimal("8.0"),
            num_crew=3,
            crew_hourly_rate=Decimal("50.00"),
            is_weekend=True,
            weekend_multiplier=Decimal("2.0")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Weekend rate: 8 * 3 * 50 * 2.0 = 2400
        assert result.labor_cost == Decimal("2400.00")
    
    def test_emergency_job(self):
        """Test calculation for emergency job."""
        inputs = EstimateCalculation(
            work_hours=Decimal("4.0"),
            num_crew=3,
            crew_hourly_rate=Decimal("50.00"),
            is_emergency=True,
            emergency_multiplier=Decimal("3.0")
        )
        
        result = TreeServiceCalculator.calculate(inputs)
        
        # Emergency rate: 4 * 3 * 50 * 3.0 = 1800
        assert result.labor_cost == Decimal("1800.00")


class TestCalculatorValidation:
    """Test input validation."""
    
    def test_max_crew_size(self):
        """Test maximum crew size validation."""
        with pytest.raises(ValueError, match="crew size"):
            inputs = EstimateCalculation(
                work_hours=Decimal("4.0"),
                num_crew=11  # Max is 10
            )
    
    def test_max_work_hours(self):
        """Test maximum work hours validation."""
        with pytest.raises(ValueError, match="work hours"):
            inputs = EstimateCalculation(
                work_hours=Decimal("17.0"),  # Max is 16
                num_crew=2
            )
    
    def test_max_travel_distance(self):
        """Test maximum travel distance validation."""
        with pytest.raises(ValueError, match="travel distance"):
            inputs = EstimateCalculation(
                work_hours=Decimal("4.0"),
                num_crew=2,
                travel_distance_miles=Decimal("501.0")  # Max is 500
            )
    
    def test_percentage_bounds(self):
        """Test percentage validation."""
        with pytest.raises(ValueError):
            inputs = EstimateCalculation(
                work_hours=Decimal("4.0"),
                num_crew=2,
                overhead_percent=Decimal("101.0")  # Max is 100
            )