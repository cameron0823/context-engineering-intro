"""
Estimate schemas for request/response validation.
"""
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator, EmailStr
import re

from src.models.estimate import EstimateStatus
from src.schemas.calculation import CalculationInput, CalculationResult


class EstimateBase(BaseModel):
    """Base schema for estimates."""
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_address: Optional[str] = None
    
    job_address: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=1)
    scheduled_date: Optional[date] = None
    
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    
    @validator('customer_phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not re.match(r'^\+?1?\d{9,15}$', v):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('scheduled_date')
    def validate_scheduled_date(cls, v):
        """Ensure scheduled date is not in the past."""
        if v and v < date.today():
            raise ValueError('Scheduled date cannot be in the past')
        return v


class EstimateCreate(EstimateBase):
    """Schema for creating an estimate."""
    calculation_input: CalculationInput
    valid_days: int = Field(default=30, ge=1, le=365)
    
    @validator('valid_days')
    def validate_valid_days(cls, v):
        """Ensure validity period is reasonable."""
        if v > 365:
            raise ValueError('Validity period cannot exceed 365 days')
        return v


class EstimateUpdate(BaseModel):
    """Schema for updating an estimate (only draft/pending)."""
    customer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_address: Optional[str] = None
    
    job_address: Optional[str] = Field(None, min_length=1)
    job_description: Optional[str] = Field(None, min_length=1)
    scheduled_date: Optional[date] = None
    
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    
    # Allow recalculation
    calculation_input: Optional[CalculationInput] = None
    
    @validator('customer_phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not re.match(r'^\+?1?\d{9,15}$', v):
            raise ValueError('Invalid phone number format')
        return v


class EstimateStatusUpdate(BaseModel):
    """Schema for updating estimate status."""
    status: EstimateStatus
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('status')
    def validate_status_transition(cls, v):
        """Validate status transitions."""
        # Additional validation will be done at the service level
        # based on current status
        return v


class EstimateApproval(BaseModel):
    """Schema for approving an estimate."""
    approval_notes: Optional[str] = Field(None, max_length=1000)


class EstimateRejection(BaseModel):
    """Schema for rejecting an estimate."""
    reason: str = Field(..., min_length=1, max_length=1000)


class EstimateResponse(EstimateBase):
    """Schema for estimate responses."""
    id: int
    estimate_number: str
    status: EstimateStatus
    valid_until: date
    
    # Calculation summary
    calculation_id: str
    travel_cost: Decimal
    labor_cost: Decimal
    equipment_cost: Decimal
    disposal_fees: Decimal
    permit_cost: Decimal
    direct_costs: Decimal
    overhead_amount: Decimal
    safety_buffer_amount: Decimal
    profit_amount: Decimal
    subtotal: Decimal
    final_total: Decimal
    
    # Metadata
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime]
    
    # Approval info (if approved)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    
    # Invoice info (if invoiced)
    invoice_id: Optional[str] = None
    invoiced_at: Optional[datetime] = None
    
    # Flags
    is_editable: bool
    is_valid: bool
    can_approve: bool
    can_invoice: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }


class EstimateDetailResponse(EstimateResponse):
    """Detailed estimate response with full calculation breakdown."""
    calculation_inputs: Dict[str, Any]
    calculation_result: CalculationResult
    calculation_checksum: str
    
    # Rejection info (if rejected)
    rejected_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }


class EstimateListResponse(BaseModel):
    """Schema for paginated estimate list."""
    estimates: List[EstimateResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class EstimateCustomerView(BaseModel):
    """Schema for customer-facing estimate view."""
    estimate_number: str
    date: datetime
    valid_until: date
    customer_name: str
    job_address: str
    job_description: str
    scheduled_date: Optional[date]
    
    breakdown: Dict[str, str]  # String representations of costs
    status: str
    customer_notes: Optional[str]
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class EstimateFilter(BaseModel):
    """Schema for filtering estimates."""
    status: Optional[EstimateStatus] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    is_valid: Optional[bool] = None
    
    @validator('min_amount', 'max_amount')
    def validate_amounts(cls, v):
        """Ensure amounts are positive."""
        if v is not None and v < 0:
            raise ValueError('Amount must be positive')
        return v


class EstimateDuplicate(BaseModel):
    """Schema for duplicating an estimate."""
    update_customer_info: bool = Field(default=False)
    new_customer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    new_job_address: Optional[str] = Field(None, min_length=1)
    new_job_description: Optional[str] = Field(None, min_length=1)
    recalculate: bool = Field(default=True)
    
    @validator('new_customer_name')
    def validate_customer_name(cls, v, values):
        """Ensure customer name is provided if updating info."""
        if values.get('update_customer_info') and not v:
            raise ValueError('New customer name required when updating customer info')
        return v