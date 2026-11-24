"""
LexFlow AI - Compliance Management Service Logic.

Handles organization-level relationship validation, automated overdue detection,
audit logging, and dashboard metric aggregations.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    AuditLog,
    ComplianceControl,
    ComplianceTask,
    Contract,
    Obligation,
    TaskPriority,
    TaskStatus,
    User,
)
from app.schemas.compliance import (
    ComplianceControlResponse,
    ComplianceDashboardResponse,
    ComplianceTaskResponse,
)


def validate_task_related_entities(
    db: Session,
    organization_id: uuid.UUID,
    control_id: Optional[uuid.UUID] = None,
    contract_id: Optional[uuid.UUID] = None,
    obligation_id: Optional[uuid.UUID] = None,
    assignee_id: Optional[uuid.UUID] = None,
) -> None:
    """
    Validates that any referenced control, contract, obligation, or assigned user
    exists and belongs strictly to the authenticated user's organization.
    Raises 400 Bad Request if any entity is missing or from another tenant.
    """
    if control_id:
        control = db.execute(
            select(ComplianceControl).where(
                ComplianceControl.id == control_id,
                ComplianceControl.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if control is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Related compliance control '{control_id}' not found in your organization.",
            )

    if contract_id:
        contract = db.execute(
            select(Contract).where(
                Contract.id == contract_id,
                Contract.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if contract is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Related contract '{contract_id}' not found in your organization.",
            )

    if obligation_id:
        obligation = db.execute(
            select(Obligation).where(
                Obligation.id == obligation_id,
                Obligation.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if obligation is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Related obligation '{obligation_id}' not found in your organization.",
            )

    if assignee_id:
        assignee = db.execute(
            select(User).where(
                User.id == assignee_id,
                User.organization_id == organization_id,
            )
        ).scalar_one_or_none()
        if assignee is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assigned user '{assignee_id}' not found in your organization.",
            )


def check_and_update_overdue(
    task: ComplianceTask,
    db: Optional[Session] = None,
    user_id: Optional[uuid.UUID] = None,
) -> bool:
    """
    Determines if a task's due date has passed without completion.
    Automatically sets status to 'overdue' if due_date < today and status != completed.
    Returns True if the task was transitioned to overdue.
    """
    if task.status == TaskStatus.COMPLETED.value:
        return False

    if task.due_date and task.due_date < date.today():
        if task.status != TaskStatus.OVERDUE.value:
            task.status = TaskStatus.OVERDUE.value
            if db:
                if user_id:
                    audit = AuditLog(
                        organization_id=task.organization_id,
                        user_id=user_id,
                        action=AuditAction.UPDATE.value,
                        entity_type="ComplianceTask",
                        entity_id=task.id,
                        details={
                            "event": "task_marked_overdue",
                            "title": task.title,
                            "due_date": str(task.due_date),
                        },
                    )
                    db.add(audit)
                db.commit()
            return True

    return False


def build_task_response(task: ComplianceTask) -> ComplianceTaskResponse:
    """Builds a ComplianceTaskResponse ensuring assigned_to_id alias is populated."""
    return ComplianceTaskResponse(
        id=task.id,
        organization_id=task.organization_id,
        control_id=task.control_id,
        contract_id=task.contract_id,
        obligation_id=task.obligation_id,
        assignee_id=task.assignee_id,
        assigned_to_id=task.assignee_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def build_control_response(control: ComplianceControl, tasks_count: int = 0) -> ComplianceControlResponse:
    """Builds a ComplianceControlResponse including requirement alias and task count."""
    return ComplianceControlResponse(
        id=control.id,
        organization_id=control.organization_id,
        control_code=control.control_code,
        name=control.name,
        description=control.description,
        framework=control.framework,
        category=control.category,
        requirement=control.control_code,  # Requirement reference maps cleanly
        status=control.status,
        created_at=control.created_at,
        updated_at=control.updated_at,
        tasks_count=tasks_count,
    )


def compute_compliance_dashboard(
    db: Session,
    organization_id: uuid.UUID,
) -> ComplianceDashboardResponse:
    """
    Computes tenant-scoped dashboard metrics:
    - Total, pending, in-progress, completed, and overdue tasks.
    - Tasks grouped by priority.
    - Tasks due within the next 7 days.
    - Compliance controls count.
    - Overall completion percentage.
    """
    # 1. Fetch all tasks for organization
    tasks = db.execute(
        select(ComplianceTask).where(ComplianceTask.organization_id == organization_id)
    ).scalars().all()

    # 2. Controls count
    controls_count = db.scalar(
        select(func.count(ComplianceControl.id)).where(
            ComplianceControl.organization_id == organization_id
        )
    ) or 0

    today = date.today()
    next_7_days = today + timedelta(days=7)

    pending_count = 0
    in_progress_count = 0
    completed_count = 0
    overdue_count = 0
    due_next_7_days_count = 0

    priority_counts: Dict[str, int] = {
        TaskPriority.LOW.value: 0,
        TaskPriority.MEDIUM.value: 0,
        TaskPriority.HIGH.value: 0,
        TaskPriority.CRITICAL.value: 0,
    }

    for task in tasks:
        # Evaluate dynamic overdue
        is_overdue = False
        if task.status != TaskStatus.COMPLETED.value and task.due_date and task.due_date < today:
            is_overdue = True

        status_val = task.status.lower()

        if status_val == TaskStatus.COMPLETED.value:
            completed_count += 1
        elif is_overdue or status_val == TaskStatus.OVERDUE.value:
            overdue_count += 1
        elif status_val in (TaskStatus.IN_PROGRESS.value, TaskStatus.UNDER_REVIEW.value):
            in_progress_count += 1
        else:
            pending_count += 1

        # Priority grouping
        p_val = task.priority.lower() if task.priority else TaskPriority.MEDIUM.value
        if p_val == TaskPriority.URGENT.value:
            p_val = TaskPriority.CRITICAL.value
        if p_val in priority_counts:
            priority_counts[p_val] += 1
        else:
            priority_counts[p_val] = 1

        # Tasks due within next 7 days (and not completed)
        if task.due_date and status_val != TaskStatus.COMPLETED.value:
            if today <= task.due_date <= next_7_days:
                due_next_7_days_count += 1

    total_tasks = len(tasks)
    completion_percentage = (
        round((completed_count / total_tasks) * 100.0, 2) if total_tasks > 0 else 0.0
    )

    return ComplianceDashboardResponse(
        total_tasks=total_tasks,
        pending_tasks=pending_count,
        in_progress_tasks=in_progress_count,
        completed_tasks=completed_count,
        overdue_tasks=overdue_count,
        tasks_by_priority=priority_counts,
        tasks_due_next_7_days=due_next_7_days_count,
        compliance_controls_count=controls_count,
        completion_percentage=completion_percentage,
    )
