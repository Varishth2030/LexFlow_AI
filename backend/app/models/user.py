import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.contract import Contract
    from app.models.compliance import ComplianceTask
    from app.models.audit_log import AuditLog


class User(Base, UUIDMixin, TimestampMixin):
    """
    User entity belonging to an organization with role-based permissions.
    """

    __tablename__ = "users"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        default=UserRole.MEMBER.value,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="users",
    )
    created_contracts: Mapped[List["Contract"]] = relationship(
        "Contract",
        back_populates="creator",
        foreign_keys="Contract.created_by_id",
    )
    assigned_tasks: Mapped[List["ComplianceTask"]] = relationship(
        "ComplianceTask",
        back_populates="assignee",
        foreign_keys="ComplianceTask.assignee_id",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.id})>"
