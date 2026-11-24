import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, computed_field


class DocumentChunkResponse(BaseModel):
    """
    Response schema for document chunk information.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: Optional[int] = None
    page_number: Optional[int] = None
    embedding_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ContractResponse(BaseModel):
    """
    Standard contract summary response schema.
    Explicitly excludes internal filesystem paths (file_path).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_by_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    contract_type: str
    status: str
    file_hash: Optional[str] = None
    file_size_bytes: Optional[int] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ContractDetailResponse(ContractResponse):
    """
    Detailed contract response including chunk counts and extracted chunks.
    """

    document_chunks_count: int = 0
    document_chunks: Optional[List[DocumentChunkResponse]] = None


class ContractListResponse(BaseModel):
    """
    Paginated list of contracts for the current tenant.
    """

    items: List[ContractResponse]
    total: int
    skip: int
    limit: int

    @computed_field
    @property
    def contracts(self) -> List[ContractResponse]:
        """Convenience property for frontend clients expecting a 'contracts' array."""
        return self.items


class ContractDeleteResponse(BaseModel):
    """
    Response schema confirming successful contract deletion.
    """

    message: str = "Contract deleted successfully."
    id: uuid.UUID


class ContractSearchRequest(BaseModel):
    """
    Search request parameters for deterministic contract chunk retrieval.
    """

    query: str
    contract_id: Optional[uuid.UUID] = None
    skip: int = 0
    limit: int = 20


class ContractSearchItem(BaseModel):
    """
    Verbatim passage retrieved from a contract chunk.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    contract_title: str
    contract_type: str
    chunk_index: int
    page_number: Optional[int] = None
    matched_clause_type: Optional[str] = None
    snippet: str
    exact_match_score: float
    responsible_party: Optional[str] = None
    source_reference: Optional[str] = None


class ContractSearchResponse(BaseModel):
    """
    Response schema for deterministic contract search results.
    """

    items: List[ContractSearchItem]
    total: int
    skip: int
    limit: int
    query: str
    message: str
    legal_disclaimer: str

    @computed_field
    @property
    def results(self) -> List[ContractSearchItem]:
        """Convenience property for frontend clients expecting a 'results' array."""
        return self.items

