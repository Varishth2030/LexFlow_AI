import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import RiskCategory, RiskSeverity, RiskStatus

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.organization import Organization
    from app.models.clause import Clause


class RiskAssessment(Base, UUIDMixin, TimestampMixin):
    """
    Identified legal, operational, financial, or compliance risk within a contract or specific clause.
    """

    __tablename__ = "risk_assessments"

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
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50),
        default=RiskSeverity.MEDIUM.value,
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        default=RiskCategory.LEGAL.value,
        nullable=False,
        index=True,
    )
    mitigation_strategy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=RiskStatus.IDENTIFIED.value,
        nullable=False,
        index=True,
    )

    # Relationships
    contract: Mapped["Contract"] = relationship(
        "Contract",
        back_populates="risk_assessments",
    )
    organization: Mapped["Organization"] = relationship("Organization")
    clause: Mapped[Optional["Clause"]] = relationship(
        "Clause",
        back_populates="risk_assessments",
    )

    def __repr__(self) -> str:
        return f"<RiskAssessment '{self.title}' severity={self.severity} ({self.id})>"
