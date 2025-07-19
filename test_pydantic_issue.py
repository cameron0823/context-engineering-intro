"""Test script to identify Pydantic issues in costs.py"""
import sys
import warnings

# Capture all warnings
warnings.filterwarnings("error")

try:
    print("Testing Pydantic imports and model creation...")
    
    # Test 1: Import the schemas
    from src.schemas.costs import LaborRateUpdate, LaborRateResponse
    print("✅ Import successful")
    
    # Test 2: Create an instance
    update_data = {
        "hourly_rate": 50.00,
        "description": "Test update"
    }
    update = LaborRateUpdate(**update_data)
    print(f"✅ LaborRateUpdate instance created: {update}")
    
    # Test 3: Check for Field validation
    from pydantic import Field
    from decimal import Decimal
    
    # Test if Field parameters work correctly
    test_field = Field(None, ge=0, decimal_places=2)
    print("✅ Field validation parameters work")
    
except DeprecationWarning as e:
    print(f"❌ Deprecation Warning: {e}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Check for common issues
print("\n🔍 Checking for common Pydantic v2 migration issues...")

# Check if ConfigDict is being used
try:
    with open("src/schemas/costs.py", "r") as f:
        content = f.read()
        
    issues = []
    
    if "@validator" in content:
        issues.append("- Using @validator (deprecated) instead of @field_validator")
    
    if "class Config:" in content:
        issues.append("- Using 'class Config:' instead of 'model_config = ConfigDict(...)'")
        
    if "from pydantic import ConfigDict" not in content and "model_config" in content:
        issues.append("- Missing 'from pydantic import ConfigDict' import")
    
    if issues:
        print("⚠️  Found Pydantic v1 syntax that should be updated:")
        for issue in issues:
            print(issue)
    else:
        print("✅ No obvious Pydantic v1 syntax issues found")
        
except Exception as e:
    print(f"Could not analyze file: {e}")