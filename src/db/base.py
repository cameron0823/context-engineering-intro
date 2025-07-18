"""
Database base configuration.
Import all models here to ensure they are registered with SQLAlchemy.
"""
from src.models.base import Base
from src.models.user import User
from src.models.audit import AuditLog
from src.models.costs import (
    LaborRate, EquipmentCost, OverheadSettings,
    VehicleRate, DisposalFee, SeasonalAdjustment
)
from src.models.estimate import Estimate

# This ensures all models are imported and registered
__all__ = [
    "Base",
    "User",
    "AuditLog", 
    "LaborRate",
    "EquipmentCost",
    "OverheadSettings",
    "VehicleRate",
    "DisposalFee",
    "SeasonalAdjustment",
    "Estimate"
]