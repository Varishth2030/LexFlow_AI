import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ControlFramework, ControlStatus, TaskPriority, TaskStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.contract import Contract
    from app.models.obligation import Obligation


class ComplianceControl(Base, UUIDMixin, TimestampMixin):
    """
    Standard compliance requirement / control definition (e.g. SOC2, ISO27001, GDPR).
    Scoped to an organization.
    """

    __tablename__ = "compliance_controls"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    framework: Mapped[str] = mapped_column(
        String(100),
        default=ControlFramework.INTERNAL.value,
        nullable=False,
        index=True,
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=ControlStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="compliance_controls",
    )
    compliance_tasks: Mapped[List["ComplianceTask"]] = relationship(
        "ComplianceTask",
        back_populates="control",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "control_code", name="uq_compliance_control_code"),
    )

    def __repr__(self) -> str:
        return f"<ComplianceControl {self.control_code} ({self.id})>"


class ComplianceTask(Base, UUIDMixin, TimestampMixin):
    """
    Actionable remediation, review, or recurring audit task fulfilling a compliance control,
    contractual obligation, or contract review.
    """

    __tablename__ = "compliance_tasks"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("compliance_controls.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    contract_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contracts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    obligation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("obligations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=TaskStatus.TODO.value,
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(50),
        default=TaskPriority.MEDIUM.value,
        nullable=False,
        index=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="compliance_tasks",
    )
    control: Mapped[Optional["ComplianceControl"]] = relationship(
        "ComplianceControl",
        back_populates="compliance_tasks",
    )
    contract: Mapped[Optional["Contract"]] = relationship(
        "Contract",
        back_populates="compliance_tasks",
    )
    obligation: Mapped[Optional["Obligation"]] = relationship(
        "Obligation",
        back_populates="compliance_tasks",
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assignee_id],
    )

    def __repr__(self) -> str:
        return f"<ComplianceTask '{self.title}' status={self.status} ({self.id})>"
