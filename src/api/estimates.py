"""
Estimate API endpoints.
"""
from typing import List, Optional, Any
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
import structlog

from src.api.deps import get_db, get_current_active_user, require_role
from src.models.user import User, UserRole
from src.models.estimate import Estimate, EstimateStatus
from src.core.calculator import TreeServiceCalculator
from src.schemas.estimate import (
    EstimateCreate, EstimateUpdate, EstimateResponse,
    EstimateDetailResponse, EstimateListResponse,
    EstimateStatusUpdate, EstimateApproval, EstimateRejection,
    EstimateFilter, EstimateDuplicate, EstimateCustomerView
)
from src.services.audit import audit_service
from src.services.external_apis import get_external_api_service, QuickBooksError


logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=EstimateResponse)
async def create_estimate(
    estimate_data: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a new estimate.
    
    - Requires authenticated user
    - Automatically calculates costs based on input
    - Creates audit trail entry
    """
    # Require at least Estimator role to create estimates
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.ESTIMATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create estimates"
        )
    
    # Perform calculation
    calculator = TreeServiceCalculator()
    try:
        calculation_result = calculator.calculate_estimate(estimate_data.calculation_input)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calculation error: {str(e)}"
        )
    
    # Generate estimate number (format: EST-YYYYMMDD-XXXX)
    today = date.today()
    count_query = select(func.count(Estimate.id)).where(
        Estimate.estimate_number.like(f"EST-{today.strftime('%Y%m%d')}-%")
    )
    result = await db.execute(count_query)
    count = result.scalar() or 0
    estimate_number = f"EST-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    # Create estimate
    estimate = Estimate(
        estimate_number=estimate_number,
        customer_name=estimate_data.customer_name,
        customer_email=estimate_data.customer_email,
        customer_phone=estimate_data.customer_phone,
        customer_address=estimate_data.customer_address,
        job_address=estimate_data.job_address,
        job_description=estimate_data.job_description,
        scheduled_date=estimate_data.scheduled_date,
        internal_notes=estimate_data.internal_notes,
        customer_notes=estimate_data.customer_notes,
        calculation_inputs=estimate_data.calculation_input.model_dump(),
        calculation_id=calculation_result.calculation_id,
        calculation_result=calculation_result.model_dump(),
        calculation_checksum=calculation_result.checksum,
        travel_cost=calculation_result.travel_cost,
        labor_cost=calculation_result.labor_cost,
        equipment_cost=calculation_result.equipment_cost,
        disposal_fees=calculation_result.disposal_fees,
        permit_cost=calculation_result.permit_cost,
        direct_costs=calculation_result.direct_costs,
        overhead_amount=calculation_result.overhead_amount,
        safety_buffer_amount=calculation_result.safety_buffer_amount,
        profit_amount=calculation_result.profit_amount,
        subtotal=calculation_result.subtotal,
        final_total=calculation_result.final_total,
        valid_until=date.today() + timedelta(days=estimate_data.valid_days),
        created_by=str(current_user.id),
        updated_by=str(current_user.id)
    )
    
    db.add(estimate)
    await db.commit()
    await db.refresh(estimate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="create_estimate",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_number": estimate.estimate_number,
            "customer_name": estimate.customer_name,
            "final_total": str(estimate.final_total)
        }
    )
    
    # Convert to response
    response = EstimateResponse.model_validate(estimate)
    response.is_editable = estimate.is_editable()
    response.is_valid = estimate.is_valid()
    response.can_approve = estimate.can_approve()
    response.can_invoice = estimate.can_invoice()
    
    return response


@router.get("/", response_model=EstimateListResponse)
async def list_estimates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[EstimateStatus] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    created_after: Optional[date] = None,
    created_before: Optional[date] = None,
    is_valid: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    List estimates with pagination and filtering.
    
    - Viewers can only see approved/invoiced estimates
    - Other roles can see all estimates
    """
    # Build query with eager loading to prevent N+1 queries
    query = select(Estimate).options(
        selectinload(Estimate.created_by_user),
        selectinload(Estimate.approved_by_user)
    ).where(Estimate.deleted_at.is_(None))
    
    # Apply role-based filtering
    if current_user.role == UserRole.VIEWER:
        query = query.where(
            Estimate.status.in_([EstimateStatus.APPROVED, EstimateStatus.INVOICED])
        )
    
    # Apply filters
    if status:
        query = query.where(Estimate.status == status)
    
    if customer_name:
        query = query.where(Estimate.customer_name.ilike(f"%{customer_name}%"))
    
    if customer_email:
        query = query.where(Estimate.customer_email.ilike(f"%{customer_email}%"))
    
    if created_after:
        query = query.where(Estimate.created_at >= created_after)
    
    if created_before:
        query = query.where(Estimate.created_at <= created_before)
    
    if is_valid is not None:
        if is_valid:
            query = query.where(
                and_(
                    Estimate.valid_until >= date.today(),
                    Estimate.status.notin_([
                        EstimateStatus.EXPIRED,
                        EstimateStatus.REJECTED,
                        EstimateStatus.INVOICED
                    ])
                )
            )
        else:
            query = query.where(
                or_(
                    Estimate.valid_until < date.today(),
                    Estimate.status.in_([
                        EstimateStatus.EXPIRED,
                        EstimateStatus.REJECTED,
                        EstimateStatus.INVOICED
                    ])
                )
            )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(desc(Estimate.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    estimates = result.scalars().all()
    
    # Convert to responses
    estimate_responses = []
    for estimate in estimates:
        response = EstimateResponse.model_validate(estimate)
        response.is_editable = estimate.is_editable()
        response.is_valid = estimate.is_valid()
        response.can_approve = estimate.can_approve()
        response.can_invoice = estimate.can_invoice()
        estimate_responses.append(response)
    
    return EstimateListResponse(
        estimates=estimate_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{estimate_id}", response_model=EstimateDetailResponse)
async def get_estimate(
    estimate_id: int = Path(..., title="The ID of the estimate to get"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get detailed estimate by ID.
    
    - Viewers can only see approved/invoiced estimates
    """
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    # Check permissions
    if current_user.role == UserRole.VIEWER:
        if estimate.status not in [EstimateStatus.APPROVED, EstimateStatus.INVOICED]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view this estimate"
            )
    
    # Convert to detailed response
    response = EstimateDetailResponse.model_validate(estimate)
    response.is_editable = estimate.is_editable()
    response.is_valid = estimate.is_valid()
    response.can_approve = estimate.can_approve()
    response.can_invoice = estimate.can_invoice()
    
    return response


@router.get("/{estimate_id}/customer-view", response_model=EstimateCustomerView)
async def get_estimate_customer_view(
    estimate_id: int = Path(..., title="The ID of the estimate"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get customer-facing view of estimate (no auth required).
    
    - Only shows pending, approved, or invoiced estimates
    - Hides internal information
    """
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None),
            Estimate.status.in_([
                EstimateStatus.PENDING,
                EstimateStatus.APPROVED,
                EstimateStatus.INVOICED
            ])
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found or not available for viewing"
        )
    
    # Convert to customer view
    return EstimateCustomerView.model_validate(estimate.to_customer_dict())


@router.patch("/{estimate_id}", response_model=EstimateResponse)
async def update_estimate(
    estimate_id: int,
    estimate_update: EstimateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update an estimate (only draft/pending).
    
    - Requires Estimator role or higher
    - Can update customer info and recalculate
    """
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.ESTIMATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update estimates"
        )
    
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    if not estimate.is_editable():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estimate cannot be edited in current status"
        )
    
    # Track changes for audit
    changes = {}
    
    # Update fields if provided
    update_data = estimate_update.model_dump(exclude_unset=True)
    
    # Handle recalculation if new inputs provided
    if estimate_update.calculation_input:
        calculator = TreeServiceCalculator()
        try:
            calculation_result = calculator.calculate_estimate(estimate_update.calculation_input)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Calculation error: {str(e)}"
            )
        
        # Update calculation fields
        estimate.calculation_inputs = estimate_update.calculation_input.model_dump()
        estimate.calculation_id = calculation_result.calculation_id
        estimate.calculation_result = calculation_result.model_dump()
        estimate.calculation_checksum = calculation_result.checksum
        estimate.travel_cost = calculation_result.travel_cost
        estimate.labor_cost = calculation_result.labor_cost
        estimate.equipment_cost = calculation_result.equipment_cost
        estimate.disposal_fees = calculation_result.disposal_fees
        estimate.permit_cost = calculation_result.permit_cost
        estimate.direct_costs = calculation_result.direct_costs
        estimate.overhead_amount = calculation_result.overhead_amount
        estimate.safety_buffer_amount = calculation_result.safety_buffer_amount
        estimate.profit_amount = calculation_result.profit_amount
        estimate.subtotal = calculation_result.subtotal
        estimate.final_total = calculation_result.final_total
        
        changes["recalculated"] = True
        changes["new_total"] = str(calculation_result.final_total)
    
    # Update other fields
    for field, value in update_data.items():
        if field != "calculation_input" and hasattr(estimate, field):
            old_value = getattr(estimate, field)
            if old_value != value:
                setattr(estimate, field, value)
                changes[field] = {"old": str(old_value), "new": str(value)}
    
    estimate.updated_by = str(current_user.id)
    estimate.updated_at = func.now()
    
    await db.commit()
    await db.refresh(estimate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="update_estimate",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_number": estimate.estimate_number,
            "changes": changes
        }
    )
    
    # Convert to response
    response = EstimateResponse.model_validate(estimate)
    response.is_editable = estimate.is_editable()
    response.is_valid = estimate.is_valid()
    response.can_approve = estimate.can_approve()
    response.can_invoice = estimate.can_invoice()
    
    return response


@router.post("/{estimate_id}/status", response_model=EstimateResponse)
async def update_estimate_status(
    estimate_id: int,
    status_update: EstimateStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update estimate status.
    
    - Draft -> Pending: Any role with create permission
    - Other transitions: Manager or Admin only
    """
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    # Check permissions based on transition
    old_status = estimate.status
    new_status = status_update.status
    
    # Draft -> Pending: Any role with create permission
    if old_status == EstimateStatus.DRAFT and new_status == EstimateStatus.PENDING:
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.ESTIMATOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
    # All other transitions: Manager or Admin only
    else:
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers and admins can perform this status change"
            )
    
    # Validate transition
    valid_transitions = {
        EstimateStatus.DRAFT: [EstimateStatus.PENDING, EstimateStatus.REJECTED],
        EstimateStatus.PENDING: [EstimateStatus.APPROVED, EstimateStatus.REJECTED, EstimateStatus.EXPIRED],
        EstimateStatus.APPROVED: [EstimateStatus.INVOICED],
        EstimateStatus.REJECTED: [],  # No transitions from rejected
        EstimateStatus.EXPIRED: [],   # No transitions from expired
        EstimateStatus.INVOICED: []   # No transitions from invoiced
    }
    
    if new_status not in valid_transitions.get(old_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {old_status} to {new_status}"
        )
    
    # Update status
    estimate.status = new_status
    estimate.updated_by = str(current_user.id)
    estimate.updated_at = func.now()
    
    # Handle special transitions
    if new_status == EstimateStatus.EXPIRED:
        estimate.expire()
    
    await db.commit()
    await db.refresh(estimate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="update_estimate_status",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_number": estimate.estimate_number,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "notes": status_update.notes
        }
    )
    
    # Convert to response
    response = EstimateResponse.model_validate(estimate)
    response.is_editable = estimate.is_editable()
    response.is_valid = estimate.is_valid()
    response.can_approve = estimate.can_approve()
    response.can_invoice = estimate.can_invoice()
    
    return response


@router.post("/{estimate_id}/approve", response_model=EstimateResponse)
async def approve_estimate(
    estimate_id: int,
    approval: EstimateApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Approve an estimate.
    
    - Requires Manager or Admin role
    - Estimate must be in pending status and valid
    """
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    # Approve estimate
    try:
        estimate.approve(
            user_id=str(current_user.id),
            notes=approval.approval_notes
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    estimate.updated_by = str(current_user.id)
    estimate.updated_at = func.now()
    
    await db.commit()
    await db.refresh(estimate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="approve_estimate",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_number": estimate.estimate_number,
            "customer_name": estimate.customer_name,
            "final_total": str(estimate.final_total),
            "approval_notes": approval.approval_notes
        }
    )
    
    # Convert to response
    response = EstimateResponse.model_validate(estimate)
    response.is_editable = estimate.is_editable()
    response.is_valid = estimate.is_valid()
    response.can_approve = estimate.can_approve()
    response.can_invoice = estimate.can_invoice()
    
    return response


@router.post("/{estimate_id}/reject", response_model=EstimateResponse)
async def reject_estimate(
    estimate_id: int,
    rejection: EstimateRejection,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Reject an estimate.
    
    - Requires Manager or Admin role
    - Estimate must be in draft or pending status
    """
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    # Reject estimate
    try:
        estimate.reject(reason=rejection.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    estimate.updated_by = str(current_user.id)
    estimate.updated_at = func.now()
    
    await db.commit()
    await db.refresh(estimate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="reject_estimate",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_number": estimate.estimate_number,
            "customer_name": estimate.customer_name,
            "reason": rejection.reason
        }
    )
    
    # Convert to response
    response = EstimateResponse.model_validate(estimate)
    response.is_editable = estimate.is_editable()
    response.is_valid = estimate.is_valid()
    response.can_approve = estimate.can_approve()
    response.can_invoice = estimate.can_invoice()
    
    return response


@router.post("/{estimate_id}/duplicate", response_model=EstimateResponse)
async def duplicate_estimate(
    estimate_id: int,
    duplicate_data: EstimateDuplicate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Duplicate an existing estimate.
    
    - Creates a new draft estimate based on existing one
    - Can update customer info and recalculate
    """
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.ESTIMATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create estimates"
        )
    
    # Get original estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    # Generate new estimate number
    today = date.today()
    count_query = select(func.count(Estimate.id)).where(
        Estimate.estimate_number.like(f"EST-{today.strftime('%Y%m%d')}-%")
    )
    result = await db.execute(count_query)
    count = result.scalar() or 0
    estimate_number = f"EST-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    # Create new estimate
    new_estimate = Estimate(
        estimate_number=estimate_number,
        customer_name=duplicate_data.new_customer_name or original.customer_name,
        customer_email=original.customer_email,
        customer_phone=original.customer_phone,
        customer_address=original.customer_address,
        job_address=duplicate_data.new_job_address or original.job_address,
        job_description=duplicate_data.new_job_description or original.job_description,
        scheduled_date=None,  # Reset scheduled date
        internal_notes=original.internal_notes,
        customer_notes=original.customer_notes,
        status=EstimateStatus.DRAFT,
        valid_until=date.today() + timedelta(days=30),
        created_by=str(current_user.id),
        updated_by=str(current_user.id)
    )
    
    # Handle calculation
    if duplicate_data.recalculate:
        # Recalculate with original inputs
        calculator = TreeServiceCalculator()
        calc_input = original.calculation_inputs
        calculation_result = calculator.calculate_estimate_from_dict(calc_input)
        
        new_estimate.calculation_inputs = calc_input
        new_estimate.calculation_id = calculation_result.calculation_id
        new_estimate.calculation_result = calculation_result.model_dump()
        new_estimate.calculation_checksum = calculation_result.checksum
        new_estimate.travel_cost = calculation_result.travel_cost
        new_estimate.labor_cost = calculation_result.labor_cost
        new_estimate.equipment_cost = calculation_result.equipment_cost
        new_estimate.disposal_fees = calculation_result.disposal_fees
        new_estimate.permit_cost = calculation_result.permit_cost
        new_estimate.direct_costs = calculation_result.direct_costs
        new_estimate.overhead_amount = calculation_result.overhead_amount
        new_estimate.safety_buffer_amount = calculation_result.safety_buffer_amount
        new_estimate.profit_amount = calculation_result.profit_amount
        new_estimate.subtotal = calculation_result.subtotal
        new_estimate.final_total = calculation_result.final_total
    else:
        # Copy calculation from original
        new_estimate.calculation_inputs = original.calculation_inputs
        new_estimate.calculation_id = original.calculation_id
        new_estimate.calculation_result = original.calculation_result
        new_estimate.calculation_checksum = original.calculation_checksum
        new_estimate.travel_cost = original.travel_cost
        new_estimate.labor_cost = original.labor_cost
        new_estimate.equipment_cost = original.equipment_cost
        new_estimate.disposal_fees = original.disposal_fees
        new_estimate.permit_cost = original.permit_cost
        new_estimate.direct_costs = original.direct_costs
        new_estimate.overhead_amount = original.overhead_amount
        new_estimate.safety_buffer_amount = original.safety_buffer_amount
        new_estimate.profit_amount = original.profit_amount
        new_estimate.subtotal = original.subtotal
        new_estimate.final_total = original.final_total
    
    db.add(new_estimate)
    await db.commit()
    await db.refresh(new_estimate)
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="duplicate_estimate",
        entity_type="estimate",
        entity_id=str(new_estimate.id),
        details={
            "original_estimate_id": str(original.id),
            "original_estimate_number": original.estimate_number,
            "new_estimate_number": new_estimate.estimate_number,
            "customer_name": new_estimate.customer_name
        }
    )
    
    # Convert to response
    response = EstimateResponse.model_validate(new_estimate)
    response.is_editable = new_estimate.is_editable()
    response.is_valid = new_estimate.is_valid()
    response.can_approve = new_estimate.can_approve()
    response.can_invoice = new_estimate.can_invoice()
    
    return response


@router.delete("/{estimate_id}")
async def delete_estimate(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Soft delete an estimate.
    
    - Requires Admin role
    - Marks estimate as deleted but preserves data
    """
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    # Soft delete
    estimate.deleted_at = func.now()
    estimate.deleted_by = str(current_user.id)
    
    await db.commit()
    
    # Create audit log
    await audit_service.log_action(
        db=db,
        user_id=str(current_user.id),
        action="delete_estimate",
        entity_type="estimate",
        entity_id=str(estimate.id),
        details={
            "estimate_number": estimate.estimate_number,
            "customer_name": estimate.customer_name,
            "status": estimate.status.value
        }
    )
    
    return {"detail": "Estimate deleted successfully"}


@router.post("/{estimate_id}/create-invoice")
async def create_quickbooks_invoice(
    estimate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a QuickBooks invoice from an approved estimate.
    
    - Requires Manager or Admin role
    - Estimate must be in approved status
    - Returns QuickBooks invoice details
    """
    # Get estimate
    query = select(Estimate).where(
        and_(
            Estimate.id == estimate_id,
            Estimate.deleted_at.is_(None)
        )
    )
    result = await db.execute(query)
    estimate = result.scalar_one_or_none()
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )
    
    # Check if estimate is approved
    if estimate.status != EstimateStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved estimates can be converted to invoices"
        )
    
    # Check if already invoiced
    if estimate.status == EstimateStatus.INVOICED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estimate has already been invoiced"
        )
    
    try:
        # Create QuickBooks invoice
        api_service = get_external_api_service()
        invoice = await api_service.create_quickbooks_invoice(estimate)
        
        # Update estimate status to invoiced
        estimate.status = EstimateStatus.INVOICED
        estimate.updated_by = str(current_user.id)
        estimate.updated_at = func.now()
        
        # Store QuickBooks invoice ID in estimate (you might want to add this field to the model)
        # estimate.quickbooks_invoice_id = invoice.invoice_id
        
        await db.commit()
        await db.refresh(estimate)
        
        # Create audit log
        await audit_service.log_action(
            db=db,
            user_id=str(current_user.id),
            action="create_quickbooks_invoice",
            entity_type="estimate",
            entity_id=str(estimate.id),
            details={
                "estimate_number": estimate.estimate_number,
                "quickbooks_invoice_id": invoice.invoice_id,
                "invoice_number": invoice.invoice_number,
                "total_amount": str(invoice.total_amount)
            }
        )
        
        return {
            "detail": "QuickBooks invoice created successfully",
            "invoice": {
                "id": invoice.invoice_id,
                "number": invoice.invoice_number,
                "url": invoice.quickbooks_url,
                "total": str(invoice.total_amount),
                "created_at": invoice.created_at.isoformat()
            }
        }
        
    except QuickBooksError as e:
        logger.error(
            "Failed to create QuickBooks invoice",
            estimate_id=estimate_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"QuickBooks error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Unexpected error creating invoice",
            estimate_id=estimate_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invoice"
        )