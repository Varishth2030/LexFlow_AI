import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ClauseType, RiskSeverity

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.organization import Organization
    from app.models.obligation import Obligation
    from app.models.risk_assessment import RiskAssessment


class Clause(Base, UUIDMixin, TimestampMixin):
    """
    Extracted clause from a contract (e.g., Indemnification, Confidentiality, Termination).
    Can have associated obligations and risk assessments.
    """

    __tablename__ = "clauses"

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
    clause_type: Mapped[str] = mapped_column(
        String(100),
        default=ClauseType.GENERAL.value,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str] = mapped_column(
        String(50),
        default=RiskSeverity.LOW.value,
        nullable=False,
        index=True,
    )

    # Relationships
    contract: Mapped["Contract"] = relationship(
        "Contract",
        back_populates="clauses",
    )
    organization: Mapped["Organization"] = relationship("Organization")
    obligations: Mapped[List["Obligation"]] = relationship(
        "Obligation",
        back_populates="clause",
    )
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="clause",
    )

    def __repr__(self) -> str:
        return f"<Clause '{self.title}' type={self.clause_type} ({self.id})>"
