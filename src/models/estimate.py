"""
Estimate model for managing tree service quotes.
"""
from enum import Enum
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Enum as SQLEnum,
    Numeric, JSON, DateTime, Date, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import BaseModel


class EstimateStatus(str, Enum):
    """Status of an estimate."""
    DRAFT = "draft"
    PENDING = "pending"        # Waiting for customer response
    APPROVED = "approved"      # Customer approved
    REJECTED = "rejected"      # Customer rejected
    EXPIRED = "expired"        # Past validity period
    INVOICED = "invoiced"      # Converted to invoice


class Estimate(BaseModel):
    """Estimate model with calculation details and status tracking."""
    __tablename__ = "estimates"
    
    # Estimate number (unique identifier for customers)
    estimate_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    customer_address = Column(Text, nullable=True)
    
    # Job information
    job_address = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    scheduled_date = Column(Date, nullable=True)
    
    # Calculation inputs (stored for historical reference)
    calculation_inputs = Column(JSON, nullable=False)
    
    # Calculation results
    calculation_id = Column(String(36), nullable=False, index=True)  # UUID from calculator
    calculation_result = Column(JSON, nullable=False)
    calculation_checksum = Column(String(64), nullable=False)  # For verification
    
    # Financial summary
    travel_cost = Column(Numeric(10, 2), nullable=False)
    labor_cost = Column(Numeric(10, 2), nullable=False)
    equipment_cost = Column(Numeric(10, 2), nullable=False)
    disposal_fees = Column(Numeric(10, 2), default=Decimal("0.00"))
    permit_cost = Column(Numeric(10, 2), default=Decimal("0.00"))
    
    # Margins and totals
    direct_costs = Column(Numeric(10, 2), nullable=False)
    overhead_amount = Column(Numeric(10, 2), nullable=False)
    safety_buffer_amount = Column(Numeric(10, 2), nullable=False)
    profit_amount = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    final_total = Column(Numeric(10, 2), nullable=False)  # Rounded to $5
    
    # Status and workflow
    status = Column(
        SQLEnum(EstimateStatus),
        default=EstimateStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Validity period
    valid_until = Column(Date, nullable=False)
    
    # Approval tracking
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Rejection tracking
    rejected_reason = Column(Text, nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Invoice tracking
    invoice_id = Column(String(50), nullable=True)  # QuickBooks invoice ID
    invoiced_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    internal_notes = Column(Text, nullable=True)  # Not shown to customer
    customer_notes = Column(Text, nullable=True)  # Shown on estimate
    
    # Relationships
    created_by_user = relationship("User", foreign_keys=[BaseModel.created_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_estimate_status_date', 'status', 'created_at'),
        Index('idx_estimate_customer', 'customer_name', 'customer_email'),
        Index('idx_estimate_valid_until', 'valid_until', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<Estimate(id={self.id}, number={self.estimate_number}, status={self.status})>"
    
    def is_editable(self) -> bool:
        """Check if estimate can be edited."""
        return self.status in [EstimateStatus.DRAFT, EstimateStatus.PENDING]
    
    def is_valid(self) -> bool:
        """Check if estimate is still valid."""
        if self.status in [EstimateStatus.EXPIRED, EstimateStatus.REJECTED, EstimateStatus.INVOICED]:
            return False
        return date.today() <= self.valid_until
    
    def can_approve(self) -> bool:
        """Check if estimate can be approved."""
        return self.status == EstimateStatus.PENDING and self.is_valid()
    
    def can_invoice(self) -> bool:
        """Check if estimate can be converted to invoice."""
        return self.status == EstimateStatus.APPROVED and not self.invoice_id
    
    def approve(self, user_id: str, notes: Optional[str] = None) -> None:
        """Approve the estimate."""
        if not self.can_approve():
            raise ValueError("Estimate cannot be approved in current state")
        
        self.status = EstimateStatus.APPROVED
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        self.approval_notes = notes
    
    def reject(self, reason: str) -> None:
        """Reject the estimate."""
        if self.status not in [EstimateStatus.PENDING, EstimateStatus.DRAFT]:
            raise ValueError("Estimate cannot be rejected in current state")
        
        self.status = EstimateStatus.REJECTED
        self.rejected_reason = reason
        self.rejected_at = datetime.utcnow()
    
    def mark_invoiced(self, invoice_id: str) -> None:
        """Mark estimate as invoiced."""
        if not self.can_invoice():
            raise ValueError("Estimate cannot be invoiced in current state")
        
        self.status = EstimateStatus.INVOICED
        self.invoice_id = invoice_id
        self.invoiced_at = datetime.utcnow()
    
    def expire(self) -> None:
        """Mark estimate as expired."""
        if self.status in [EstimateStatus.APPROVED, EstimateStatus.INVOICED]:
            raise ValueError("Cannot expire approved or invoiced estimate")
        
        self.status = EstimateStatus.EXPIRED
    
    def to_customer_dict(self) -> dict:
        """
        Convert to dictionary for customer view (hide internal details).
        """
        return {
            "estimate_number": self.estimate_number,
            "date": self.created_at.isoformat() if self.created_at else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "customer_name": self.customer_name,
            "job_address": self.job_address,
            "job_description": self.job_description,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "breakdown": {
                "travel_cost": str(self.travel_cost),
                "labor_cost": str(self.labor_cost),
                "equipment_cost": str(self.equipment_cost),
                "disposal_fees": str(self.disposal_fees),
                "permit_cost": str(self.permit_cost),
                "subtotal": str(self.subtotal),
                "final_total": str(self.final_total)
            },
            "status": self.status.value if self.status else None,
            "customer_notes": self.customer_notes
        }