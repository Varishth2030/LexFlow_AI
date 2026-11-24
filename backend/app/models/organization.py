from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.contract import Contract
    from app.models.compliance import ComplianceControl, ComplianceTask
    from app.models.audit_log import AuditLog


class Organization(Base, UUIDMixin, TimestampMixin):
    """
    Root multi-tenant entity representing a customer organization / company.
    All business data is scoped to an organization.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    contracts: Mapped[List["Contract"]] = relationship(
        "Contract",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    compliance_controls: Mapped[List["ComplianceControl"]] = relationship(
        "ComplianceControl",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    compliance_tasks: Mapped[List["ComplianceTask"]] = relationship(
        "ComplianceTask",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization {self.slug} ({self.id})>"
