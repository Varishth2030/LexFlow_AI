import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models import AuditLog, User
from app.schemas.audit import AuditLogItemResponse, AuditLogListResponse

router = APIRouter()


@router.get(
    "",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List organization audit logs",
    description="Retrieves an append-only audit trail for the authenticated user's organization with optional action, entity, user, and date range filters.",
)
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by event action (e.g. CREATE, VIEW, UPDATE, DELETE, LOGIN)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (e.g. Contract, ComplianceTask, User)"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this timestamp (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this timestamp (ISO 8601)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AuditLogListResponse:
    # 1. Base filter strictly enforcing multi-tenant isolation
    base_filter = [AuditLog.organization_id == current_user.organization_id]

    if action and action.strip() and action.strip().lower() != "all":
        base_filter.append(AuditLog.action.ilike(action.strip()))

    if entity_type and entity_type.strip() and entity_type.strip().lower() != "all":
        base_filter.append(AuditLog.entity_type.ilike(entity_type.strip()))

    if user_id:
        base_filter.append(AuditLog.user_id == user_id)

    if start_date:
        base_filter.append(AuditLog.created_at >= start_date)

    if end_date:
        base_filter.append(AuditLog.created_at <= end_date)

    # 2. Count total records matching filters
    total = db.scalar(select(func.count(AuditLog.id)).where(*base_filter)) or 0

    # 3. Retrieve paginated audit logs joined with User to display actor name
    query = (
        select(AuditLog, User.full_name, User.email)
        .outerjoin(User, User.id == AuditLog.user_id)
        .where(*base_filter)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = db.execute(query).all()

    items = [
        AuditLogItemResponse(
            id=log.id,
            organization_id=log.organization_id,
            user_id=log.user_id,
            user_name=user_full_name if user_full_name else (user_email if user_email else "System Actor"),
            user_email=user_email,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details if log.details is not None else {},
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )
        for log, user_full_name, user_email in rows
    ]

    return AuditLogListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )
