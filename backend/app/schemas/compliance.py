"""
LexFlow AI - Pydantic Schemas for Milestone 6: Compliance Management Module.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import ControlFramework, ControlStatus, TaskPriority, TaskStatus


# ---------------------------------------------------------------------------
# Compliance Control Schemas
# ---------------------------------------------------------------------------

class ComplianceControlBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable control name")
    description: str = Field(..., description="Detailed description of the control requirement")
    category: Optional[str] = Field(None, max_length=100, description="Compliance category (e.g. Access Control)")
    requirement: Optional[str] = Field(None, max_length=255, description="Specific standard or requirement reference")
    framework: Optional[str] = Field(ControlFramework.INTERNAL.value, max_length=100, description="Compliance framework (SOC2, ISO27001, etc.)")
    status: Optional[str] = Field(ControlStatus.ACTIVE.value, description="Status: active or inactive")


class ComplianceControlCreate(ComplianceControlBase):
    control_code: Optional[str] = Field(None, max_length=100, description="Unique code identifier (auto-generated if omitted)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if v is None:
            return ControlStatus.ACTIVE.value
        val = v.strip().lower()
        if val not in (ControlStatus.ACTIVE.value, ControlStatus.INACTIVE.value, ControlStatus.DRAFT.value, ControlStatus.DEPRECATED.value):
            raise ValueError("Status must be 'active' or 'inactive'")
        return val


class ComplianceControlUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    requirement: Optional[str] = None
    control_code: Optional[str] = None
    framework: Optional[str] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip().lower()
        if val not in (ControlStatus.ACTIVE.value, ControlStatus.INACTIVE.value, ControlStatus.DRAFT.value, ControlStatus.DEPRECATED.value):
            raise ValueError("Status must be 'active' or 'inactive'")
        return val


class ComplianceControlResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    control_code: str
    name: str
    description: str
    framework: str
    category: Optional[str] = None
    requirement: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    tasks_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class ComplianceControlListResponse(BaseModel):
    items: List[ComplianceControlResponse]
    total: int
    skip: int
    limit: int

    @computed_field
    @property
    def controls(self) -> List[ComplianceControlResponse]:
        return self.items


class ComplianceControlDeleteResponse(BaseModel):
    id: uuid.UUID
    message: str


# ---------------------------------------------------------------------------
# Compliance Task Schemas
# ---------------------------------------------------------------------------

class ComplianceTaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Remediation or audit task title")
    description: Optional[str] = Field(None, description="Detailed explanation of task actions")
    control_id: Optional[uuid.UUID] = Field(None, description="Related compliance control identifier")
    contract_id: Optional[uuid.UUID] = Field(None, description="Related contract identifier")
    obligation_id: Optional[uuid.UUID] = Field(None, description="Related contractual obligation identifier")
    assigned_to_id: Optional[uuid.UUID] = Field(None, description="User assigned to execute the task")
    assignee_id: Optional[uuid.UUID] = Field(None, description="Alternative field for assigned user ID")
    due_date: Optional[date] = Field(None, description="Deadline date for task completion")
    priority: Optional[str] = Field(TaskPriority.MEDIUM.value, description="Priority: low, medium, high, critical")
    status: Optional[str] = Field(TaskStatus.PENDING.value, description="Status: pending, in_progress, completed, overdue")


class ComplianceTaskCreate(ComplianceTaskBase):
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> str:
        if v is None:
            return TaskPriority.MEDIUM.value
        val = v.strip().lower()
        valid = (TaskPriority.LOW.value, TaskPriority.MEDIUM.value, TaskPriority.HIGH.value, TaskPriority.CRITICAL.value, TaskPriority.URGENT.value)
        if val not in valid:
            raise ValueError(f"Priority must be one of: {', '.join(valid)}")
        return val

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if v is None:
            return TaskStatus.PENDING.value
        val = v.strip().lower()
        valid = (TaskStatus.PENDING.value, TaskStatus.TODO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.UNDER_REVIEW.value, TaskStatus.COMPLETED.value, TaskStatus.OVERDUE.value, TaskStatus.BLOCKED.value)
        if val not in valid:
            raise ValueError(f"Status must be one of: pending, in_progress, completed, overdue")
        return val


class ComplianceTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    control_id: Optional[uuid.UUID] = None
    contract_id: Optional[uuid.UUID] = None
    obligation_id: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None
    assignee_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip().lower()
        valid = (TaskPriority.LOW.value, TaskPriority.MEDIUM.value, TaskPriority.HIGH.value, TaskPriority.CRITICAL.value, TaskPriority.URGENT.value)
        if val not in valid:
            raise ValueError(f"Priority must be one of: {', '.join(valid)}")
        return val

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        val = v.strip().lower()
        valid = (TaskStatus.PENDING.value, TaskStatus.TODO.value, TaskStatus.IN_PROGRESS.value, TaskStatus.UNDER_REVIEW.value, TaskStatus.COMPLETED.value, TaskStatus.OVERDUE.value, TaskStatus.BLOCKED.value)
        if val not in valid:
            raise ValueError(f"Status must be one of: pending, in_progress, completed, overdue")
        return val


class ComplianceTaskResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    control_id: Optional[uuid.UUID] = None
    contract_id: Optional[uuid.UUID] = None
    obligation_id: Optional[uuid.UUID] = None
    assignee_id: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceTaskListResponse(BaseModel):
    items: List[ComplianceTaskResponse]
    total: int
    skip: int
    limit: int

    @computed_field
    @property
    def tasks(self) -> List[ComplianceTaskResponse]:
        return self.items


class ComplianceTaskDeleteResponse(BaseModel):
    id: uuid.UUID
    message: str


# ---------------------------------------------------------------------------
# Compliance Dashboard Schema
# ---------------------------------------------------------------------------

class ComplianceDashboardResponse(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    tasks_by_priority: Dict[str, int]
    tasks_due_next_7_days: int
    compliance_controls_count: int
    completion_percentage: float
