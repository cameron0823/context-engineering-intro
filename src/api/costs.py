"""
Cost management API endpoints.
"""
from typing import List, Optional, Any
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.exc import IntegrityError

from src.api.deps import get_db, get_current_active_user, require_role
from src.models.user import User, UserRole
from src.models.costs import (
    LaborRate, EquipmentCost, OverheadSettings,
    VehicleRate, DisposalFee, SeasonalAdjustment
)
from src.schemas.costs import (
    LaborRateCreate, LaborRateUpdate, LaborRateResponse,
    EquipmentCostCreate, EquipmentCostUpdate, EquipmentCostResponse,
    OverheadSettingsCreate, OverheadSettingsUpdate, OverheadSettingsResponse,
    VehicleRateCreate, VehicleRateUpdate, VehicleRateResponse,
    DisposalFeeCreate, DisposalFeeUpdate, DisposalFeeResponse,
    SeasonalAdjustmentCreate, SeasonalAdjustmentUpdate, SeasonalAdjustmentResponse,
    EffectiveCostsResponse
)
from src.services.audit import audit_service

router = APIRouter()


# Labor Rate Endpoints
@router.post("/labor-rates", response_model=LaborRateResponse)
async def create_labor_rate(
    rate_data: LaborRateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new labor rate with effective dating.
    
    - Requires Manager or Admin role
    - Validates no overlapping effective dates
    """
    # Check for overlapping dates
    overlap_query = select(LaborRate).where(
        and_(
            LaborRate.role == rate_data.role,
            LaborRate.deleted_at.is_(None),
            or_(
                and_(
                    LaborRate.effective_from <= rate_data.effective_from,
                    or_(
                        LaborRate.effective_to.is_(None),
                        LaborRate.effective_to >= rate_data.effective_from
                    )
                ),
                and_(
                    rate_data.effective_to.is_not(None),
                    LaborRate.effective_from <= rate_data.effective_to,
                    or_(
                        LaborRate.effective_to.is_(None),
                        LaborRate.effective_to >= rate_data.effective_to
                    )
                )
            )
        )
    )
    
    result = await db.execute(overlap_query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Labor rate dates overlap with existing rate for this role"
        )
    
    # Create labor rate
    labor_rate = LaborRate(
        role=rate_data.role,
        hourly_rate=rate_data.hourly_rate,
        overtime_multiplier=rate_data.overtime_multiplier,
        effective_from=rate_data.effective_from,
        effective_to=rate_data.effective_to,
        notes=rate_data.notes,
        created_by=str(current_user.id),
        updated_by=str(current_user.id)
    )
    
    db.add(labor_rate)
    await db.commit()
    await db.refresh(labor_rate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="create_labor_rate",
        entity_type="labor_rate",
        entity_id=str(labor_rate.id),
        details={
            "role": labor_rate.role,
            "hourly_rate": str(labor_rate.hourly_rate),
            "effective_from": labor_rate.effective_from.isoformat()
        }
    )
    
    return LaborRateResponse.model_validate(labor_rate)


@router.get("/labor-rates", response_model=List[LaborRateResponse])
async def list_labor_rates(
    role: Optional[str] = None,
    effective_date: Optional[date] = Query(None, description="Get rates effective on this date"),
    include_inactive: bool = Query(False, description="Include inactive rates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List labor rates with optional filtering.
    """
    query = select(LaborRate).where(LaborRate.deleted_at.is_(None))
    
    if role:
        query = query.where(LaborRate.role == role)
    
    if effective_date:
        query = query.where(
            and_(
                LaborRate.effective_from <= effective_date,
                or_(
                    LaborRate.effective_to.is_(None),
                    LaborRate.effective_to >= effective_date
                )
            )
        )
    elif not include_inactive:
        # By default, show only current rates
        today = date.today()
        query = query.where(
            and_(
                LaborRate.effective_from <= today,
                or_(
                    LaborRate.effective_to.is_(None),
                    LaborRate.effective_to >= today
                )
            )
        )
    
    query = query.order_by(LaborRate.role, desc(LaborRate.effective_from))
    
    result = await db.execute(query)
    rates = result.scalars().all()
    
    return [LaborRateResponse.model_validate(rate) for rate in rates]


@router.get("/labor-rates/{rate_id}", response_model=LaborRateResponse)
async def get_labor_rate(
    rate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get a specific labor rate by ID."""
    query = select(LaborRate).where(
        and_(
            LaborRate.id == rate_id,
            LaborRate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Labor rate not found"
        )
    
    return LaborRateResponse.model_validate(rate)


@router.patch("/labor-rates/{rate_id}", response_model=LaborRateResponse)
async def update_labor_rate(
    rate_id: int,
    rate_update: LaborRateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update a labor rate.
    
    - Can only update rates that haven't started yet
    - Validates no overlapping dates
    """
    # Get labor rate
    query = select(LaborRate).where(
        and_(
            LaborRate.id == rate_id,
            LaborRate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    rate = result.scalar_one_or_none()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Labor rate not found"
        )
    
    # Check if rate has already started
    if rate.effective_from <= date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify rates that have already taken effect"
        )
    
    # Update fields
    update_data = rate_update.model_dump(exclude_unset=True)
    
    # If dates are being updated, check for overlaps
    if 'effective_from' in update_data or 'effective_to' in update_data:
        new_from = update_data.get('effective_from', rate.effective_from)
        new_to = update_data.get('effective_to', rate.effective_to)
        
        overlap_query = select(LaborRate).where(
            and_(
                LaborRate.id != rate_id,
                LaborRate.role == rate.role,
                LaborRate.deleted_at.is_(None),
                or_(
                    and_(
                        LaborRate.effective_from <= new_from,
                        or_(
                            LaborRate.effective_to.is_(None),
                            LaborRate.effective_to >= new_from
                        )
                    ),
                    and_(
                        new_to is not None,
                        LaborRate.effective_from <= new_to,
                        or_(
                            LaborRate.effective_to.is_(None),
                            LaborRate.effective_to >= new_to
                        )
                    )
                )
            )
        )
        
        result = await db.execute(overlap_query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Updated dates would overlap with existing rate"
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(rate, field, value)
    
    rate.updated_by = str(current_user.id)
    rate.updated_at = func.now()
    
    await db.commit()
    await db.refresh(rate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="update_labor_rate",
        entity_type="labor_rate",
        entity_id=str(rate.id),
        details={
            "role": rate.role,
            "updates": update_data
        }
    )
    
    return LaborRateResponse.model_validate(rate)


# Equipment Cost Endpoints
@router.post("/equipment-costs", response_model=EquipmentCostResponse)
async def create_equipment_cost(
    equipment_data: EquipmentCostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new equipment cost entry.
    
    - Requires Manager or Admin role
    """
    # Create equipment cost
    equipment = EquipmentCost(
        name=equipment_data.name,
        type=equipment_data.type,
        hourly_cost=equipment_data.hourly_cost,
        daily_cost=equipment_data.daily_cost,
        setup_cost=equipment_data.setup_cost,
        fuel_per_hour=equipment_data.fuel_per_hour,
        available=equipment_data.available,
        notes=equipment_data.notes,
        created_by=str(current_user.id),
        updated_by=str(current_user.id)
    )
    
    db.add(equipment)
    await db.commit()
    await db.refresh(equipment)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="create_equipment_cost",
        entity_type="equipment_cost",
        entity_id=str(equipment.id),
        details={
            "name": equipment.name,
            "type": equipment.type,
            "hourly_cost": str(equipment.hourly_cost)
        }
    )
    
    return EquipmentCostResponse.model_validate(equipment)


@router.get("/equipment-costs", response_model=List[EquipmentCostResponse])
async def list_equipment_costs(
    type: Optional[str] = None,
    available_only: bool = Query(True, description="Show only available equipment"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """List equipment costs with optional filtering."""
    query = select(EquipmentCost).where(EquipmentCost.deleted_at.is_(None))
    
    if type:
        query = query.where(EquipmentCost.type == type)
    
    if available_only:
        query = query.where(EquipmentCost.available == True)
    
    query = query.order_by(EquipmentCost.type, EquipmentCost.name)
    
    result = await db.execute(query)
    equipment = result.scalars().all()
    
    return [EquipmentCostResponse.model_validate(eq) for eq in equipment]


# Overhead Settings Endpoints
@router.post("/overhead-settings", response_model=OverheadSettingsResponse)
async def create_overhead_settings(
    settings_data: OverheadSettingsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create new overhead settings.
    
    - Requires Admin role
    - Validates no overlapping effective dates
    """
    # Check for overlapping dates
    overlap_query = select(OverheadSettings).where(
        and_(
            OverheadSettings.deleted_at.is_(None),
            or_(
                and_(
                    OverheadSettings.effective_from <= settings_data.effective_from,
                    or_(
                        OverheadSettings.effective_to.is_(None),
                        OverheadSettings.effective_to >= settings_data.effective_from
                    )
                ),
                and_(
                    settings_data.effective_to.is_not(None),
                    OverheadSettings.effective_from <= settings_data.effective_to,
                    or_(
                        OverheadSettings.effective_to.is_(None),
                        OverheadSettings.effective_to >= settings_data.effective_to
                    )
                )
            )
        )
    )
    
    result = await db.execute(overlap_query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Overhead settings dates overlap with existing settings"
        )
    
    # Create overhead settings
    overhead = OverheadSettings(
        base_overhead_percent=settings_data.base_overhead_percent,
        large_job_discount_percent=settings_data.large_job_discount_percent,
        large_job_threshold=settings_data.large_job_threshold,
        small_job_premium_percent=settings_data.small_job_premium_percent,
        small_job_threshold=settings_data.small_job_threshold,
        effective_from=settings_data.effective_from,
        effective_to=settings_data.effective_to,
        notes=settings_data.notes,
        created_by=str(current_user.id),
        updated_by=str(current_user.id)
    )
    
    db.add(overhead)
    await db.commit()
    await db.refresh(overhead)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="create_overhead_settings",
        entity_type="overhead_settings",
        entity_id=str(overhead.id),
        details={
            "base_overhead_percent": str(overhead.base_overhead_percent),
            "effective_from": overhead.effective_from.isoformat()
        }
    )
    
    return OverheadSettingsResponse.model_validate(overhead)


@router.get("/overhead-settings/current", response_model=OverheadSettingsResponse)
async def get_current_overhead_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get current overhead settings."""
    today = date.today()
    query = select(OverheadSettings).where(
        and_(
            OverheadSettings.deleted_at.is_(None),
            OverheadSettings.effective_from <= today,
            or_(
                OverheadSettings.effective_to.is_(None),
                OverheadSettings.effective_to >= today
            )
        )
    )
    
    result = await db.execute(query)
    settings = result.scalar_one_or_none()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No overhead settings found for current date"
        )
    
    return OverheadSettingsResponse.model_validate(settings)


# Seasonal Adjustment Endpoints
@router.post("/seasonal-adjustments", response_model=SeasonalAdjustmentResponse)
async def create_seasonal_adjustment(
    adjustment_data: SeasonalAdjustmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new seasonal adjustment.
    
    - Requires Manager or Admin role
    """
    # Create seasonal adjustment
    adjustment = SeasonalAdjustment(
        name=adjustment_data.name,
        adjustment_percent=adjustment_data.adjustment_percent,
        start_month=adjustment_data.start_month,
        start_day=adjustment_data.start_day,
        end_month=adjustment_data.end_month,
        end_day=adjustment_data.end_day,
        active=adjustment_data.active,
        notes=adjustment_data.notes,
        created_by=str(current_user.id),
        updated_by=str(current_user.id)
    )
    
    db.add(adjustment)
    await db.commit()
    await db.refresh(adjustment)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="create_seasonal_adjustment",
        entity_type="seasonal_adjustment",
        entity_id=str(adjustment.id),
        details={
            "name": adjustment.name,
            "adjustment_percent": str(adjustment.adjustment_percent),
            "period": f"{adjustment.start_month}/{adjustment.start_day} - {adjustment.end_month}/{adjustment.end_day}"
        }
    )
    
    return SeasonalAdjustmentResponse.model_validate(adjustment)


@router.get("/seasonal-adjustments", response_model=List[SeasonalAdjustmentResponse])
async def list_seasonal_adjustments(
    active_only: bool = Query(True, description="Show only active adjustments"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """List seasonal adjustments."""
    query = select(SeasonalAdjustment).where(SeasonalAdjustment.deleted_at.is_(None))
    
    if active_only:
        query = query.where(SeasonalAdjustment.active == True)
    
    query = query.order_by(SeasonalAdjustment.start_month, SeasonalAdjustment.start_day)
    
    result = await db.execute(query)
    adjustments = result.scalars().all()
    
    return [SeasonalAdjustmentResponse.model_validate(adj) for adj in adjustments]


# Effective Costs Endpoint
@router.get("/effective-costs", response_model=EffectiveCostsResponse)
async def get_effective_costs(
    effective_date: date = Query(date.today(), description="Get costs effective on this date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get all costs effective on a specific date.
    
    This is useful for historical quote recreation.
    """
    # Get labor rates
    labor_query = select(LaborRate).where(
        and_(
            LaborRate.deleted_at.is_(None),
            LaborRate.effective_from <= effective_date,
            or_(
                LaborRate.effective_to.is_(None),
                LaborRate.effective_to >= effective_date
            )
        )
    )
    labor_result = await db.execute(labor_query)
    labor_rates = labor_result.scalars().all()
    
    # Get equipment costs (always current)
    equipment_query = select(EquipmentCost).where(
        and_(
            EquipmentCost.deleted_at.is_(None),
            EquipmentCost.available == True
        )
    )
    equipment_result = await db.execute(equipment_query)
    equipment_costs = equipment_result.scalars().all()
    
    # Get overhead settings
    overhead_query = select(OverheadSettings).where(
        and_(
            OverheadSettings.deleted_at.is_(None),
            OverheadSettings.effective_from <= effective_date,
            or_(
                OverheadSettings.effective_to.is_(None),
                OverheadSettings.effective_to >= effective_date
            )
        )
    )
    overhead_result = await db.execute(overhead_query)
    overhead_settings = overhead_result.scalar_one_or_none()
    
    # Get vehicle rates
    vehicle_query = select(VehicleRate).where(
        and_(
            VehicleRate.deleted_at.is_(None),
            VehicleRate.effective_from <= effective_date,
            or_(
                VehicleRate.effective_to.is_(None),
                VehicleRate.effective_to >= effective_date
            )
        )
    )
    vehicle_result = await db.execute(vehicle_query)
    vehicle_rates = vehicle_result.scalars().all()
    
    # Get disposal fees (always current)
    disposal_query = select(DisposalFee).where(
        and_(
            DisposalFee.deleted_at.is_(None),
            DisposalFee.active == True
        )
    )
    disposal_result = await db.execute(disposal_query)
    disposal_fees = disposal_result.scalars().all()
    
    # Get seasonal adjustments (check if date falls within range)
    seasonal_query = select(SeasonalAdjustment).where(
        and_(
            SeasonalAdjustment.deleted_at.is_(None),
            SeasonalAdjustment.active == True
        )
    )
    seasonal_result = await db.execute(seasonal_query)
    all_adjustments = seasonal_result.scalars().all()
    
    # Filter seasonal adjustments by date
    active_adjustments = []
    for adj in all_adjustments:
        # Check if effective_date falls within the adjustment period
        month = effective_date.month
        day = effective_date.day
        
        if adj.start_month <= adj.end_month:
            # Normal case: adjustment doesn't span year boundary
            if (month > adj.start_month or (month == adj.start_month and day >= adj.start_day)) and \
               (month < adj.end_month or (month == adj.end_month and day <= adj.end_day)):
                active_adjustments.append(adj)
        else:
            # Adjustment spans year boundary (e.g., Dec to Feb)
            if (month > adj.start_month or (month == adj.start_month and day >= adj.start_day)) or \
               (month < adj.end_month or (month == adj.end_month and day <= adj.end_day)):
                active_adjustments.append(adj)
    
    return EffectiveCostsResponse(
        effective_date=effective_date,
        labor_rates=[LaborRateResponse.model_validate(rate) for rate in labor_rates],
        equipment_costs=[EquipmentCostResponse.model_validate(eq) for eq in equipment_costs],
        overhead_settings=OverheadSettingsResponse.model_validate(overhead_settings) if overhead_settings else None,
        vehicle_rates=[VehicleRateResponse.model_validate(rate) for rate in vehicle_rates],
        disposal_fees=[DisposalFeeResponse.model_validate(fee) for fee in disposal_fees],
        seasonal_adjustments=[SeasonalAdjustmentResponse.model_validate(adj) for adj in active_adjustments]
    )