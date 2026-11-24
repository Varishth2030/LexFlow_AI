"""
LexFlow AI - Compliance Management Endpoints.

Provides endpoints for Compliance Controls CRUD, Compliance Tasks CRUD,
dynamic overdue evaluation, audit logging, and tenant-scoped dashboard metrics.
"""

from datetime import date, datetime, timezone
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models import (
    AuditAction,
    AuditLog,
    ComplianceControl,
    ComplianceTask,
    ControlFramework,
    ControlStatus,
    TaskPriority,
    TaskStatus,
    User,
)
from app.schemas.compliance import (
    ComplianceControlCreate,
    ComplianceControlDeleteResponse,
    ComplianceControlListResponse,
    ComplianceControlResponse,
    ComplianceControlUpdate,
    ComplianceDashboardResponse,
    ComplianceTaskCreate,
    ComplianceTaskDeleteResponse,
    ComplianceTaskListResponse,
    ComplianceTaskResponse,
    ComplianceTaskUpdate,
)
from app.services.compliance_service import (
    build_control_response,
    build_task_response,
    check_and_update_overdue,
    compute_compliance_dashboard,
    validate_task_related_entities,
)

router = APIRouter()


# ==============================================================================
# Compliance Controls Endpoints
# ==============================================================================

@router.get(
    "/controls",
    response_model=ComplianceControlListResponse,
    status_code=status.HTTP_200_OK,
    summary="List compliance controls",
    description="Retrieves a paginated list of compliance controls for the authenticated organization.",
)
def list_compliance_controls(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(20, ge=1, le=100, description="Limit"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (active/inactive)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    framework: Optional[str] = Query(None, description="Filter by framework (soc2, iso27001, etc.)"),
    search: Optional[str] = Query(None, description="Search by name, code, or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceControlListResponse:
    base_filter = [ComplianceControl.organization_id == current_user.organization_id]

    if status_filter:
        base_filter.append(ComplianceControl.status == status_filter.strip().lower())
    if category:
        base_filter.append(ComplianceControl.category.ilike(f"%{category.strip()}%"))
    if framework:
        base_filter.append(ComplianceControl.framework == framework.strip().lower())
    if search and search.strip():
        term = f"%{search.strip()}%"
        base_filter.append(
            or_(
                ComplianceControl.name.ilike(term),
                ComplianceControl.control_code.ilike(term),
                ComplianceControl.description.ilike(term),
            )
        )

    # Total count
    total = db.scalar(select(func.count(ComplianceControl.id)).where(*base_filter)) or 0

    # Fetch items
    query = (
        select(ComplianceControl)
        .where(*base_filter)
        .order_by(ComplianceControl.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    controls = db.execute(query).scalars().all()

    # Pre-fetch tasks count for each control
    task_counts = {}
    if controls:
        ctrl_ids = [c.id for c in controls]
        counts_res = db.execute(
            select(ComplianceTask.control_id, func.count(ComplianceTask.id))
            .where(ComplianceTask.control_id.in_(ctrl_ids))
            .group_by(ComplianceTask.control_id)
        ).all()
        task_counts = {cid: cnt for cid, cnt in counts_res}

    items = [build_control_response(c, task_counts.get(c.id, 0)) for c in controls]

    return ComplianceControlListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/controls",
    response_model=ComplianceControlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create compliance control",
    description="Creates a new compliance control definition scoped to the authenticated organization.",
)
def create_compliance_control(
    payload: ComplianceControlCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceControlResponse:
    org_id = current_user.organization_id

    # Resolve control code: use explicit code, or requirement, or auto-generate
    if payload.control_code and payload.control_code.strip():
        code = payload.control_code.strip().upper()
    elif payload.requirement and payload.requirement.strip():
        # Clean requirement into a code if suitable or slugify
        candidate = payload.requirement.strip().upper()
        code = candidate if len(candidate) <= 100 else f"CTRL-{uuid.uuid4().hex[:8].upper()}"
    else:
        code = f"CTRL-{uuid.uuid4().hex[:8].upper()}"

    # Verify uniqueness in tenant
    existing = db.execute(
        select(ComplianceControl).where(
            ComplianceControl.organization_id == org_id,
            ComplianceControl.control_code == code,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Compliance control with code '{code}' already exists in your organization.",
        )

    control = ComplianceControl(
        id=uuid.uuid4(),
        organization_id=org_id,
        control_code=code,
        name=payload.name.strip(),
        description=payload.description.strip(),
        framework=payload.framework.strip().lower() if payload.framework else ControlFramework.INTERNAL.value,
        category=payload.category.strip() if payload.category else None,
        status=payload.status.strip().lower() if payload.status else ControlStatus.ACTIVE.value,
    )
    db.add(control)

    # Audit log
    audit = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action=AuditAction.CREATE.value,
        entity_type="ComplianceControl",
        entity_id=control.id,
        details={
            "event": "control_created",
            "name": control.name,
            "control_code": control.control_code,
            "framework": control.framework,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(control)

    return build_control_response(control, tasks_count=0)


@router.get(
    "/controls/{control_id}",
    response_model=ComplianceControlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get compliance control details",
    description="Retrieves a single compliance control by ID. Returns 404 for other organizations' controls.",
)
def get_compliance_control(
    control_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceControlResponse:
    control = db.execute(
        select(ComplianceControl).where(
            ComplianceControl.id == control_id,
            ComplianceControl.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if control is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance control not found.",
        )

    tasks_count = db.scalar(
        select(func.count(ComplianceTask.id)).where(
            ComplianceTask.control_id == control.id
        )
    ) or 0

    return build_control_response(control, tasks_count=tasks_count)


@router.patch(
    "/controls/{control_id}",
    response_model=ComplianceControlResponse,
    status_code=status.HTTP_200_OK,
    summary="Update compliance control",
    description="Updates an existing compliance control. Strictly scoped to the authenticated organization.",
)
def update_compliance_control(
    control_id: uuid.UUID,
    payload: ComplianceControlUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceControlResponse:
    control = db.execute(
        select(ComplianceControl).where(
            ComplianceControl.id == control_id,
            ComplianceControl.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if control is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance control not found.",
        )

    updated_fields = []

    if payload.name is not None and payload.name.strip():
        control.name = payload.name.strip()
        updated_fields.append("name")

    if payload.description is not None:
        control.description = payload.description.strip()
        updated_fields.append("description")

    if payload.category is not None:
        control.category = payload.category.strip() if payload.category.strip() else None
        updated_fields.append("category")

    if payload.framework is not None and payload.framework.strip():
        control.framework = payload.framework.strip().lower()
        updated_fields.append("framework")

    if payload.status is not None:
        control.status = payload.status.strip().lower()
        updated_fields.append("status")

    if payload.control_code is not None and payload.control_code.strip():
        new_code = payload.control_code.strip().upper()
        if new_code != control.control_code:
            # Check collision
            dup = db.execute(
                select(ComplianceControl).where(
                    ComplianceControl.organization_id == current_user.organization_id,
                    ComplianceControl.control_code == new_code,
                    ComplianceControl.id != control.id,
                )
            ).scalar_one_or_none()
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Control code '{new_code}' already exists in your organization.",
                )
            control.control_code = new_code
            updated_fields.append("control_code")

    # Record audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.UPDATE.value,
        entity_type="ComplianceControl",
        entity_id=control.id,
        details={
            "event": "control_updated",
            "name": control.name,
            "updated_fields": updated_fields,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(control)

    tasks_count = db.scalar(
        select(func.count(ComplianceTask.id)).where(
            ComplianceTask.control_id == control.id
        )
    ) or 0

    return build_control_response(control, tasks_count=tasks_count)


@router.delete(
    "/controls/{control_id}",
    response_model=ComplianceControlDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete compliance control",
    description="Deletes a compliance control and cascades deletion to linked child tasks.",
)
def delete_compliance_control(
    control_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceControlDeleteResponse:
    control = db.execute(
        select(ComplianceControl).where(
            ComplianceControl.id == control_id,
            ComplianceControl.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if control is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance control not found.",
        )

    # Audit log before deletion
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.DELETE.value,
        entity_type="ComplianceControl",
        entity_id=control.id,
        details={
            "event": "control_deleted",
            "name": control.name,
            "control_code": control.control_code,
        },
    )
    db.add(audit)

    db.delete(control)
    db.commit()

    return ComplianceControlDeleteResponse(
        id=control_id,
        message="Compliance control deleted successfully.",
    )


# ==============================================================================
# Compliance Tasks Endpoints
# ==============================================================================

@router.get(
    "/tasks",
    response_model=ComplianceTaskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List compliance tasks",
    description="Retrieves a paginated list of compliance tasks with filtering and automatic overdue calculation.",
)
def list_compliance_tasks(
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(20, ge=1, le=100, description="Limit"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (pending, in_progress, completed, overdue)"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high, critical)"),
    due_date: Optional[date] = Query(None, description="Filter by exact due date"),
    control_id: Optional[uuid.UUID] = Query(None, description="Filter by related control"),
    contract_id: Optional[uuid.UUID] = Query(None, description="Filter by related contract"),
    assignee_id: Optional[uuid.UUID] = Query(None, description="Filter by assigned user"),
    search: Optional[str] = Query(None, description="Search by task title or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceTaskListResponse:
    base_filter = [ComplianceTask.organization_id == current_user.organization_id]

    if priority:
        p_val = priority.strip().lower()
        if p_val == TaskPriority.URGENT.value:
            p_val = TaskPriority.CRITICAL.value
        base_filter.append(ComplianceTask.priority == p_val)

    if due_date:
        base_filter.append(ComplianceTask.due_date == due_date)
    if control_id:
        base_filter.append(ComplianceTask.control_id == control_id)
    if contract_id:
        base_filter.append(ComplianceTask.contract_id == contract_id)
    if assignee_id:
        base_filter.append(ComplianceTask.assignee_id == assignee_id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        base_filter.append(
            or_(
                ComplianceTask.title.ilike(term),
                ComplianceTask.description.ilike(term),
            )
        )

    # Fetch tasks
    tasks = db.execute(
        select(ComplianceTask)
        .where(*base_filter)
        .order_by(ComplianceTask.created_at.desc())
    ).scalars().all()

    # Dynamic overdue evaluation for each task
    overdue_updated = False
    for t in tasks:
        if check_and_update_overdue(t):
            overdue_updated = True
    if overdue_updated:
        db.commit()

    # Apply status filter in-memory if requested to accurately include dynamically overdue tasks
    if status_filter:
        s_val = status_filter.strip().lower()
        if s_val == "pending":
            tasks = [t for t in tasks if t.status.lower() in ("pending", "todo")]
        elif s_val == "in_progress":
            tasks = [t for t in tasks if t.status.lower() in ("in_progress", "under_review")]
        else:
            tasks = [t for t in tasks if t.status.lower() == s_val]

    total = len(tasks)
    paginated_tasks = tasks[skip : skip + limit]

    return ComplianceTaskListResponse(
        items=[build_task_response(t) for t in paginated_tasks],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/tasks",
    response_model=ComplianceTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create compliance task",
    description="Creates a new compliance task, validating that all related foreign entities belong to the same organization.",
)
def create_compliance_task(
    payload: ComplianceTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceTaskResponse:
    org_id = current_user.organization_id
    assignee = payload.assignee_id or payload.assigned_to_id

    # Validate relationships are strictly within tenant
    validate_task_related_entities(
        db=db,
        organization_id=org_id,
        control_id=payload.control_id,
        contract_id=payload.contract_id,
        obligation_id=payload.obligation_id,
        assignee_id=assignee,
    )

    # Determine status & completed_at
    initial_status = payload.status.strip().lower() if payload.status else TaskStatus.PENDING.value
    completed_at = None

    if initial_status == TaskStatus.COMPLETED.value:
        completed_at = datetime.now(timezone.utc)
    elif payload.due_date and payload.due_date < date.today():
        # Automatically mark overdue if due date is in the past and not completed
        initial_status = TaskStatus.OVERDUE.value

    priority_val = payload.priority.strip().lower() if payload.priority else TaskPriority.MEDIUM.value
    if priority_val == TaskPriority.URGENT.value:
        priority_val = TaskPriority.CRITICAL.value

    task = ComplianceTask(
        id=uuid.uuid4(),
        organization_id=org_id,
        control_id=payload.control_id,
        contract_id=payload.contract_id,
        obligation_id=payload.obligation_id,
        assignee_id=assignee,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        priority=priority_val,
        status=initial_status,
        due_date=payload.due_date,
        completed_at=completed_at,
    )
    db.add(task)

    # Audit log
    audit = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action=AuditAction.CREATE.value,
        entity_type="ComplianceTask",
        entity_id=task.id,
        details={
            "event": "task_created",
            "title": task.title,
            "priority": task.priority,
            "status": task.status,
            "due_date": str(task.due_date) if task.due_date else None,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(task)

    return build_task_response(task)


@router.get(
    "/tasks/{task_id}",
    response_model=ComplianceTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get compliance task details",
    description="Retrieves a compliance task by ID, dynamically evaluating overdue status. Strictly scoped to the authenticated organization.",
)
def get_compliance_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceTaskResponse:
    task = db.execute(
        select(ComplianceTask).where(
            ComplianceTask.id == task_id,
            ComplianceTask.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance task not found.",
        )

    # Dynamically check & update overdue
    check_and_update_overdue(task, db, current_user.id)

    return build_task_response(task)


@router.patch(
    "/tasks/{task_id}",
    response_model=ComplianceTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update compliance task",
    description="Updates task properties, assignments, priority, and status. Handles completed_at and overdue transitions.",
)
def update_compliance_task(
    task_id: uuid.UUID,
    payload: ComplianceTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceTaskResponse:
    task = db.execute(
        select(ComplianceTask).where(
            ComplianceTask.id == task_id,
            ComplianceTask.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance task not found.",
        )

    org_id = current_user.organization_id
    assignee = payload.assignee_id or payload.assigned_to_id

    # Validate updated relationships
    validate_task_related_entities(
        db=db,
        organization_id=org_id,
        control_id=payload.control_id,
        contract_id=payload.contract_id,
        obligation_id=payload.obligation_id,
        assignee_id=assignee,
    )

    updated_fields = []

    if payload.title is not None and payload.title.strip():
        task.title = payload.title.strip()
        updated_fields.append("title")

    if payload.description is not None:
        task.description = payload.description.strip() if payload.description.strip() else None
        updated_fields.append("description")

    if payload.control_id is not None:
        task.control_id = payload.control_id
        updated_fields.append("control_id")

    if payload.contract_id is not None:
        task.contract_id = payload.contract_id
        updated_fields.append("contract_id")

    if payload.obligation_id is not None:
        task.obligation_id = payload.obligation_id
        updated_fields.append("obligation_id")

    if assignee is not None:
        task.assignee_id = assignee
        updated_fields.append("assignee_id")

    if payload.due_date is not None:
        task.due_date = payload.due_date
        updated_fields.append("due_date")

    if payload.priority is not None:
        p_val = payload.priority.strip().lower()
        if p_val == TaskPriority.URGENT.value:
            p_val = TaskPriority.CRITICAL.value
        task.priority = p_val
        updated_fields.append("priority")

    # Status transitions & completed/overdue evaluation
    if payload.status is not None:
        new_status = payload.status.strip().lower()
        updated_fields.append("status")

        if new_status == TaskStatus.COMPLETED.value:
            task.status = TaskStatus.COMPLETED.value
            if not task.completed_at:
                task.completed_at = datetime.now(timezone.utc)
            # Log specific task completion audit
            audit_completed = AuditLog(
                organization_id=org_id,
                user_id=current_user.id,
                action=AuditAction.UPDATE.value,
                entity_type="ComplianceTask",
                entity_id=task.id,
                details={"event": "task_marked_completed", "title": task.title},
            )
            db.add(audit_completed)
        else:
            task.completed_at = None
            task.status = new_status

    # Automated overdue evaluation if task is not completed
    if task.status != TaskStatus.COMPLETED.value and task.due_date and task.due_date < date.today():
        task.status = TaskStatus.OVERDUE.value
        updated_fields.append("status_overdue_computed")

    # General audit log
    audit = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action=AuditAction.UPDATE.value,
        entity_type="ComplianceTask",
        entity_id=task.id,
        details={
            "event": "task_updated",
            "title": task.title,
            "updated_fields": updated_fields,
            "status": task.status,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(task)

    return build_task_response(task)


@router.delete(
    "/tasks/{task_id}",
    response_model=ComplianceTaskDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete compliance task",
    description="Deletes a compliance task. Strictly scoped to the authenticated organization.",
)
def delete_compliance_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceTaskDeleteResponse:
    task = db.execute(
        select(ComplianceTask).where(
            ComplianceTask.id == task_id,
            ComplianceTask.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance task not found.",
        )

    # Audit log before deletion
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.DELETE.value,
        entity_type="ComplianceTask",
        entity_id=task.id,
        details={
            "event": "task_deleted",
            "title": task.title,
        },
    )
    db.add(audit)

    db.delete(task)
    db.commit()

    return ComplianceTaskDeleteResponse(
        id=task_id,
        message="Compliance task deleted successfully.",
    )


# ==============================================================================
# Compliance Dashboard Endpoint
# ==============================================================================

@router.get(
    "/dashboard",
    response_model=ComplianceDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get compliance dashboard metrics",
    description=(
        "Returns aggregated compliance statistics strictly for the authenticated organization: "
        "total tasks, status breakdown (pending, in_progress, completed, overdue), priority breakdown, "
        "tasks due in next 7 days, controls count, and completion percentage."
    ),
)
def get_compliance_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ComplianceDashboardResponse:
    return compute_compliance_dashboard(db=db, organization_id=current_user.organization_id)
