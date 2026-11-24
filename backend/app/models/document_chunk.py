import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, Uuid, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.organization import Organization


class DocumentChunk(Base, UUIDMixin):
    """
    Extracted textual chunk from a contract document, prepared for embedding,
    vector indexing, and RAG semantic retrieval.
    """

    __tablename__ = "document_chunks"

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
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    contract: Mapped["Contract"] = relationship(
        "Contract",
        back_populates="document_chunks",
    )
    organization: Mapped["Organization"] = relationship("Organization")

    __table_args__ = (
        Index("ix_document_chunks_contract_chunk", "contract_id", "chunk_index"),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk contract={self.contract_id} index={self.chunk_index} ({self.id})>"
