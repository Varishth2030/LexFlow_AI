from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ContractTypeCount(BaseModel):
    name: str
    count: int


class QuarterlyTrendItem(BaseModel):
    quarter: str
    critical: int
    high: int
    resolved: int


class ExecutiveReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_contracts: int
    total_clauses: int
    compliance_governance_rate: float
    total_risks: int
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    resolved_risks: int
    total_obligations: int
    pending_obligations: int
    overdue_obligations: int
    completed_obligations: int
    total_controls: int
    active_controls: int
    total_compliance_tasks: int
    completed_compliance_tasks: int
    contract_type_distribution: List[ContractTypeCount]
    risk_trend: List[QuarterlyTrendItem]
    organization_name: str
    generated_at: str
    legal_disclaimer: str
