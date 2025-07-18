"""
Rounding utilities for financial calculations.
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP


def round_to_cents(value: Decimal, rounding=ROUND_HALF_UP) -> Decimal:
    """
    Round a decimal value to 2 decimal places (cents).
    
    Args:
        value: Decimal value to round
        rounding: Rounding method (default: ROUND_HALF_UP)
        
    Returns:
        Rounded decimal value
    """
    return value.quantize(Decimal('0.01'), rounding=rounding)


def round_to_nearest_five(value: Decimal) -> Decimal:
    """
    Round a decimal value to the nearest $5.
    
    Examples:
        1232.50 -> 1235.00
        1232.49 -> 1230.00
        1235.00 -> 1235.00
        
    Args:
        value: Decimal value to round
        
    Returns:
        Value rounded to nearest $5
    """
    return (value / Decimal('5')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('5')


def round_to_nearest_ten(value: Decimal) -> Decimal:
    """
    Round a decimal value to the nearest $10.
    
    Args:
        value: Decimal value to round
        
    Returns:
        Value rounded to nearest $10
    """
    return (value / Decimal('10')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('10')


def round_down_to_five(value: Decimal) -> Decimal:
    """
    Round down to the nearest $5.
    
    Args:
        value: Decimal value to round
        
    Returns:
        Value rounded down to nearest $5
    """
    return (value / Decimal('5')).quantize(Decimal('1'), rounding=ROUND_DOWN) * Decimal('5')


def round_up_to_five(value: Decimal) -> Decimal:
    """
    Round up to the nearest $5.
    
    Args:
        value: Decimal value to round
        
    Returns:
        Value rounded up to nearest $5
    """
    return (value / Decimal('5')).quantize(Decimal('1'), rounding=ROUND_UP) * Decimal('5')


def calculate_percentage(base: Decimal, percentage: Decimal) -> Decimal:
    """
    Calculate a percentage of a base amount.
    
    Args:
        base: Base amount
        percentage: Percentage (e.g., 25.5 for 25.5%)
        
    Returns:
        Calculated percentage amount rounded to cents
    """
    result = base * (percentage / Decimal('100'))
    return round_to_cents(result)


def add_percentage(base: Decimal, percentage: Decimal) -> Decimal:
    """
    Add a percentage to a base amount.
    
    Args:
        base: Base amount
        percentage: Percentage to add (e.g., 25.5 for 25.5%)
        
    Returns:
        Base amount plus percentage, rounded to cents
    """
    addition = calculate_percentage(base, percentage)
    return round_to_cents(base + addition)


def format_currency(value: Decimal, include_cents: bool = True) -> str:
    """
    Format a decimal value as currency string.
    
    Args:
        value: Decimal value to format
        include_cents: Whether to include cents in output
        
    Returns:
        Formatted currency string (e.g., "$1,234.56")
    """
    if include_cents:
        return f"${value:,.2f}"
    else:
        # Round to whole dollars first
        whole_dollars = value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return f"${whole_dollars:,.0f}"


def parse_currency(value: str) -> Decimal:
    """
    Parse a currency string to Decimal.
    
    Args:
        value: Currency string (e.g., "$1,234.56" or "1234.56")
        
    Returns:
        Decimal value
        
    Raises:
        ValueError: If string cannot be parsed
    """
    # Remove currency symbols and commas
    cleaned = value.replace('$', '').replace(',', '').strip()
    
    try:
        return Decimal(cleaned)
    except:
        raise ValueError(f"Cannot parse '{value}' as currency")