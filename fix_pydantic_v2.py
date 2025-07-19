"""Script to fix all Pydantic v1 patterns in costs.py"""
import re

# Read the file
with open('src/schemas/costs.py', 'r') as f:
    content = f.read()

# Remove the old validator import since we already have field_validator
content = content.replace(
    "from pydantic import BaseModel, Field, field_validator, ConfigDict, validator",
    "from pydantic import BaseModel, Field, field_validator, ConfigDict"
)

# Replace all @validator with @field_validator
content = re.sub(r'@validator\(', '@field_validator(', content)

# Add @classmethod after each @field_validator
lines = content.split('\n')
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if '@field_validator(' in line and i + 1 < len(lines):
        # Check if next line is not already @classmethod
        if '@classmethod' not in lines[i + 1]:
            # Add proper indentation
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + '@classmethod')

content = '\n'.join(new_lines)

# Replace all class Config: blocks with model_config
config_pattern = r'(\s*)class Config:\s*\n(\s*)[^\n]+(?:\s*\n\2[^\n]+)*'
def replace_config(match):
    indent = match.group(1)
    config_content = match.group(0)
    
    # Extract config values
    from_attributes = 'orm_mode = True' in config_content or 'from_attributes = True' in config_content
    validate_assignment = 'validate_assignment = True' in config_content
    use_enum_values = 'use_enum_values = True' in config_content
    
    # Build model_config
    config_items = []
    if from_attributes:
        config_items.append('from_attributes=True')
    if validate_assignment:
        config_items.append('validate_assignment=True')
    if use_enum_values:
        config_items.append('use_enum_values=True')
    
    if not config_items:
        config_items.append('from_attributes=True')  # Default
    
    return f'{indent}model_config = ConfigDict(\n{indent}    {",\n{0}    ".format(indent).join(config_items)}\n{indent})'

content = re.sub(config_pattern, replace_config, content)

# Handle pre=True validators differently in v2
# In v2, we use mode='before' instead of pre=True
content = re.sub(
    r"@field_validator\((.*?),\s*pre=True\)",
    r"@field_validator(\1, mode='before')",
    content
)

# Write the fixed content
with open('src/schemas/costs.py', 'w') as f:
    f.write(content)

print("✅ Fixed all Pydantic v1 patterns!")
print("\nChanges made:")
print("- Replaced @validator with @field_validator")
print("- Added @classmethod decorators")
print("- Replaced 'class Config:' with 'model_config = ConfigDict(...)'")
print("- Updated pre=True to mode='before'")