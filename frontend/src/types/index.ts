// Common status and severity types
export type UserRole = 'owner' | 'admin' | 'manager' | 'member' | 'auditor' | 'viewer';

export type ContractStatus = 'draft' | 'under_review' | 'active' | 'expired' | 'terminated';
export type ContractType = 'msa' | 'nda' | 'dpa' | 'sla' | 'employment' | 'vendor' | 'license' | 'other';

export type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';
export type RiskBand = 'Low' | 'Medium' | 'High' | 'Critical';

export type ObligationStatus = 'pending' | 'in_progress' | 'completed' | 'breached';
export type ObligationFrequency = 'one_time' | 'monthly' | 'quarterly' | 'annual';

export type ControlStatus = 'active' | 'inactive';
export type ControlFramework = 'SOC2' | 'ISO27001' | 'GDPR' | 'HIPAA' | 'Internal';

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'overdue';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

// Auth & User Types
export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  organization?: Organization;
  message?: string;
}

// Contract & Document Chunk Types
export interface DocumentChunk {
  id: string;
  contract_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
  page_number?: number | null;
  embedding_metadata?: {
    source_type?: string;
    page_number?: number;
    char_count?: number;
    word_count?: number;
    section_index?: number;
  };
  created_at: string;
}

export interface Contract {
  id: string;
  organization_id: string;
  created_by_id?: string | null;
  title: string;
  description?: string | null;
  contract_type: ContractType;
  status: ContractStatus;
  file_hash: string;
  file_size_bytes: number;
  effective_date?: string | null;
  expiration_date?: string | null;
  metadata_json?: {
    source_type?: string;
    page_count?: number;
    total_characters?: number;
    total_chunks?: number;
    original_filename?: string;
    content_type?: string;
  };
  created_at: string;
  updated_at: string;
  document_chunks_count?: number;
  document_chunks?: DocumentChunk[];
}

export interface ContractListResponse {
  total: number;
  skip: number;
  limit: number;
  items: Contract[];
  contracts?: Contract[];
}

// Clause Types
export interface Clause {
  id: string;
  contract_id: string;
  clause_type: string;
  title: string;
  text: string;
  risk_level: RiskSeverity;
  page_number?: number | null;
  rule_match_indicator?: number;
  section_index?: number;
  created_at?: string;
}

// Risk Assessment Types
export interface RiskAssessment {
  id: string;
  contract_id: string;
  clause_id?: string | null;
  rule_id: string;
  title: string;
  risk_score: number;
  severity: RiskSeverity;
  category: string;
  description: string;
  evidence_text?: string | null;
  mitigation_strategy?: string | null;
  created_at?: string;
  contract_title?: string;
  contract_type?: string;
}

export interface RiskListResponse {
  contract_id: string;
  items: RiskAssessment[];
  total: number;
  total_risk_score: number;
  risk_band: string;
  severity_distribution: Record<string, number>;
  legal_disclaimer: string;
}

export interface OrganizationRiskListResponse {
  items: RiskAssessment[];
  total: number;
  skip: number;
  limit: number;
  overall_risk_score: number;
  risk_band: string;
  severity_distribution: Record<string, number>;
  legal_disclaimer: string;
}

// Obligation Types
export interface Obligation {
  id: string;
  contract_id: string;
  clause_id?: string | null;
  contract_title?: string;
  contract_type?: string;
  title: string;
  description?: string;
  responsible_party: string;
  due_date?: string | null;
  deadline_type?: 'exact' | 'relative' | 'none';
  relative_deadline_text?: string | null;
  frequency: ObligationFrequency;
  status: ObligationStatus;
  priority?: TaskPriority;
  created_at?: string;
}

export interface ObligationListResponse {
  contract_id: string;
  items: Obligation[];
  total: number;
}

export interface OrganizationObligationListResponse {
  items: Obligation[];
  total: number;
  skip: number;
  limit: number;
}

// Complete Analysis Types
export interface ContractAnalysis {
  contract_id: string;
  clauses_count: number;
  risks_count: number;
  obligations_count: number;
  overall_risk_score: number;
  risk_band: RiskBand;
  severity_distribution: Record<RiskSeverity, number>;
  legal_disclaimer: string;
  clauses: Clause[];
  risks: RiskAssessment[];
  obligations: Obligation[];
}

// Compliance Types
export interface ComplianceControl {
  id: string;
  organization_id: string;
  control_code: string;
  name: string;
  description?: string | null;
  category: string;
  framework?: ControlFramework | string;
  requirement?: string | null;
  status: ControlStatus;
  tasks_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ComplianceTask {
  id: string;
  organization_id: string;
  control_id?: string | null;
  control_code?: string | null;
  control_name?: string | null;
  contract_id?: string | null;
  contract_title?: string | null;
  obligation_id?: string | null;
  assignee_id?: string | null;
  assigned_to_id?: string | null;
  assignee_name?: string | null;
  title: string;
  description?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComplianceDashboard {
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  tasks_by_priority: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  tasks_due_next_7_days: number;
  compliance_controls_count: number;
  completion_percentage: number;
}

// Audit Log Types
export interface AuditLog {
  id: string;
  organization_id?: string | null;
  user_id?: string | null;
  user_name?: string;
  user_email?: string;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  details?: Record<string, any>;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  skip: number;
  limit: number;
  logs?: AuditLog[];
}

// Search Assistant Result Types
export interface SearchResultPassage {
  id: string;
  contract_id: string;
  contract_title: string;
  contract_type: string;
  chunk_index: number;
  page_number?: number | null;
  matched_clause_type?: string;
  snippet: string;
  exact_match_score: number;
  responsible_party?: string;
  source_reference?: string;
}

export interface ContractSearchResponse {
  items: SearchResultPassage[];
  total: number;
  skip: number;
  limit: number;
  query: string;
  message: string;
  legal_disclaimer: string;
  results?: SearchResultPassage[];
}

// Executive Reports & Analytics Types
export interface ContractTypeDistribution {
  name: string;
  count: number;
}

export interface RiskTrendItem {
  quarter: string;
  critical: number;
  high: number;
  resolved: number;
}

export interface ExecutiveReportSummary {
  total_contracts: number;
  total_clauses: number;
  compliance_governance_rate: number;
  total_risks: number;
  critical_risks: number;
  high_risks: number;
  medium_risks: number;
  low_risks: number;
  resolved_risks: number;
  total_obligations: number;
  pending_obligations: number;
  overdue_obligations: number;
  completed_obligations: number;
  total_controls: number;
  active_controls: number;
  total_compliance_tasks: number;
  completed_compliance_tasks: number;
  contract_type_distribution: ContractTypeDistribution[];
  risk_trend: RiskTrendItem[];
  organization_name: string;
  generated_at: string;
  legal_disclaimer: string;
}
