"""
LexFlow AI - Pydantic Schemas for Milestone 5: Contract Analysis Engine.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ClauseResponse(BaseModel):
    """Schema for detected clause data."""

    id: uuid.UUID
    contract_id: uuid.UUID
    organization_id: uuid.UUID
    clause_type: str
    title: str
    text: str
    page_number: Optional[int] = None
    risk_level: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentResponse(BaseModel):
    """Schema for risk assessment findings."""

    id: uuid.UUID
    contract_id: uuid.UUID
    organization_id: uuid.UUID
    clause_id: Optional[uuid.UUID] = None
    title: str
    description: str
    risk_score: float
    severity: str
    category: str
    mitigation_strategy: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObligationResponse(BaseModel):
    """Schema for contractual obligation records."""

    id: uuid.UUID
    contract_id: uuid.UUID
    organization_id: uuid.UUID
    clause_id: Optional[uuid.UUID] = None
    title: str
    description: str
    responsible_party: str
    due_date: Optional[date] = None
    frequency: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskScoreSummary(BaseModel):
    """Aggregated risk score and severity breakdown."""

    total_risk_score: float = Field(..., description="Sum of weighted risk severity scores")
    risk_band: str = Field(..., description="Normalized risk classification: Low, Medium, High, or Critical")
    severity_distribution: Dict[str, int] = Field(..., description="Counts of risks by severity level")
    total_risks_identified: int = Field(..., description="Total count of identified legal/operational risks")
    legal_disclaimer: str = Field(..., description="Mandatory screening disclaimer")


class ContractAnalysisResponse(BaseModel):
    """Comprehensive contract analysis response combining clauses, risks, and obligations."""

    contract_id: uuid.UUID
    organization_id: uuid.UUID
    contract_title: str
    analysis_timestamp: datetime
    risk_score_summary: RiskScoreSummary
    clauses_count: int
    risks_count: int
    obligations_count: int
    clauses: List[ClauseResponse]
    risks: List[RiskAssessmentResponse]
    obligations: List[ObligationResponse]
    legal_disclaimer: str

    model_config = ConfigDict(from_attributes=True)


class RiskListResponse(BaseModel):
    """Response schema for contract risks list endpoint."""

    contract_id: uuid.UUID
    items: List[RiskAssessmentResponse]
    total: int
    total_risk_score: float
    risk_band: str
    severity_distribution: Dict[str, int]
    legal_disclaimer: str


class ObligationListResponse(BaseModel):
    """Response schema for contract obligations list endpoint."""

    contract_id: uuid.UUID
    items: List[ObligationResponse]
    total: int


class OrganizationRiskItemResponse(BaseModel):
    """Schema for organization-wide risk findings with contract context."""

    id: uuid.UUID
    contract_id: uuid.UUID
    organization_id: uuid.UUID
    clause_id: Optional[uuid.UUID] = None
    title: str
    description: str
    risk_score: float
    severity: str
    category: str
    mitigation_strategy: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    contract_title: Optional[str] = None
    contract_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationRiskListResponse(BaseModel):
    """Response schema for organization-wide risks list endpoint."""

    items: List[OrganizationRiskItemResponse]
    total: int
    skip: int
    limit: int
    overall_risk_score: float
    risk_band: str
    severity_distribution: Dict[str, int]
    legal_disclaimer: str


class OrganizationObligationItemResponse(BaseModel):
    """Schema for organization-wide obligations with contract context."""

    id: uuid.UUID
    contract_id: uuid.UUID
    organization_id: uuid.UUID
    clause_id: Optional[uuid.UUID] = None
    title: str
    description: str
    responsible_party: str
    due_date: Optional[date] = None
    frequency: str
    status: str
    created_at: datetime
    updated_at: datetime
    contract_title: Optional[str] = None
    contract_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationObligationListResponse(BaseModel):
    """Response schema for organization-wide obligations list endpoint."""

    items: List[OrganizationObligationItemResponse]
    total: int
    skip: int
    limit: int

