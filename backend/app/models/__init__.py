"""
LexFlow AI Models Package.

Re-exports the declarative Base and all 10 core domain models to ensure
Alembic migrations and application services can discover all table metadata.
"""

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.organization import Organization
from app.models.user import User
from app.models.contract import Contract
from app.models.document_chunk import DocumentChunk
from app.models.clause import Clause
from app.models.risk_assessment import RiskAssessment
from app.models.obligation import Obligation
from app.models.compliance import ComplianceControl, ComplianceTask
from app.models.audit_log import AuditLog
from app.models.enums import (
    AuditAction,
    ClauseType,
    ContractStatus,
    ContractType,
    ControlFramework,
    ControlStatus,
    ObligationFrequency,
    ObligationStatus,
    RiskCategory,
    RiskSeverity,
    RiskStatus,
    TaskPriority,
    TaskStatus,
    UserRole,
)

__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "Organization",
    "User",
    "Contract",
    "DocumentChunk",
    "Clause",
    "RiskAssessment",
    "Obligation",
    "ComplianceControl",
    "ComplianceTask",
    "AuditLog",
    # Enums
    "AuditAction",
    "ClauseType",
    "ContractStatus",
    "ContractType",
    "ControlFramework",
    "ControlStatus",
    "ObligationFrequency",
    "ObligationStatus",
    "RiskCategory",
    "RiskSeverity",
    "RiskStatus",
    "TaskPriority",
    "TaskStatus",
    "UserRole",
]
