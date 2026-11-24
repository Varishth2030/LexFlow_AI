import uuid
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ContractStatus, ContractType

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.document_chunk import DocumentChunk
    from app.models.clause import Clause
    from app.models.risk_assessment import RiskAssessment
    from app.models.obligation import Obligation
    from app.models.compliance import ComplianceTask


class Contract(Base, UUIDMixin, TimestampMixin):
    """
    Contract entity representing an uploaded, analyzed, or managed legal agreement.
    Scoped directly to an organization.
    """

    __tablename__ = "contracts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contract_type: Mapped[str] = mapped_column(
        String(50),
        default=ContractType.OTHER.value,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=ContractStatus.DRAFT.value,
        nullable=False,
        index=True,
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="contracts",
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="created_contracts",
        foreign_keys=[created_by_id],
    )
    document_chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="contract",
        cascade="all, delete-orphan",
    )
    clauses: Mapped[List["Clause"]] = relationship(
        "Clause",
        back_populates="contract",
        cascade="all, delete-orphan",
    )
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="contract",
        cascade="all, delete-orphan",
    )
    obligations: Mapped[List["Obligation"]] = relationship(
        "Obligation",
        back_populates="contract",
        cascade="all, delete-orphan",
    )
    compliance_tasks: Mapped[List["ComplianceTask"]] = relationship(
        "ComplianceTask",
        back_populates="contract",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Contract '{self.title}' status={self.status} ({self.id})>"
