import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ObligationFrequency, ObligationStatus

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.organization import Organization
    from app.models.clause import Clause
    from app.models.compliance import ComplianceTask


class Obligation(Base, UUIDMixin, TimestampMixin):
    """
    Actionable contractual obligation, deliverable, or milestone extracted from contracts.
    """

    __tablename__ = "obligations"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clause_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clauses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_party: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    frequency: Mapped[str] = mapped_column(
        String(50),
        default=ObligationFrequency.ONE_TIME.value,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=ObligationStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # Relationships
    contract: Mapped["Contract"] = relationship(
        "Contract",
        back_populates="obligations",
    )
    organization: Mapped["Organization"] = relationship("Organization")
    clause: Mapped[Optional["Clause"]] = relationship(
        "Clause",
        back_populates="obligations",
    )
    compliance_tasks: Mapped[List["ComplianceTask"]] = relationship(
        "ComplianceTask",
        back_populates="obligation",
    )

    def __repr__(self) -> str:
        return f"<Obligation '{self.title}' status={self.status} ({self.id})>"
