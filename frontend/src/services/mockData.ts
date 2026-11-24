import { 
  Contract, 
  Clause, 
  RiskAssessment, 
  Obligation, 
  ComplianceControl, 
  ComplianceTask, 
  ComplianceDashboard, 
  AuditLog,
  SearchResultPassage
} from '../types';

export const DEMO_CONTRACTS: Contract[] = [
  {
    id: 'c-101-msa-apex',
    organization_id: 'org-demo-lexflow',
    created_by_id: 'usr-1',
    title: 'Master Services Agreement (Apex Global Systems)',
    description: 'Enterprise IT infrastructure deployment and 24/7 managed support agreement.',
    contract_type: 'msa',
    status: 'active',
    file_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    file_size_bytes: 2458900,
    effective_date: '2026-01-15',
    expiration_date: '2027-01-14',
    metadata_json: {
      source_type: 'pdf',
      page_count: 8,
      total_characters: 18450,
      total_chunks: 19,
      original_filename: 'Apex_Global_MSA_2026.pdf',
      content_type: 'application/pdf',
    },
    created_at: '2026-01-15T10:30:00Z',
    updated_at: '2026-01-16T14:20:00Z',
    document_chunks_count: 19,
  },
  {
    id: 'c-102-nda-zenith',
    organization_id: 'org-demo-lexflow',
    created_by_id: 'usr-1',
    title: 'Mutual Non-Disclosure Agreement (Zenith BioTech)',
    description: 'Bilateral confidentiality agreement covering joint patent evaluation.',
    contract_type: 'nda',
    status: 'active',
    file_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    file_size_bytes: 412000,
    effective_date: '2026-02-01',
    expiration_date: '2028-02-01',
    metadata_json: {
      source_type: 'pdf',
      page_count: 3,
      total_characters: 6200,
      total_chunks: 7,
      original_filename: 'Zenith_Mutual_NDA_Signed.pdf',
      content_type: 'application/pdf',
    },
    created_at: '2026-02-01T09:15:00Z',
    updated_at: '2026-02-01T09:15:00Z',
    document_chunks_count: 7,
  },
  {
    id: 'c-103-dpa-cloud',
    organization_id: 'org-demo-lexflow',
    created_by_id: 'usr-2',
    title: 'Data Processing Addendum (CloudScale AI Europe)',
    description: 'GDPR and EU Standard Contractual Clauses (SCCs) for cross-border data transfer.',
    contract_type: 'dpa',
    status: 'under_review',
    file_hash: '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b',
    file_size_bytes: 1820400,
    effective_date: '2026-03-10',
    expiration_date: '2027-03-09',
    metadata_json: {
      source_type: 'docx',
      page_count: 12,
      total_characters: 24100,
      total_chunks: 25,
      original_filename: 'CloudScale_DPA_Addendum_v3.docx',
      content_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    },
    created_at: '2026-03-10T11:45:00Z',
    updated_at: '2026-03-11T16:00:00Z',
    document_chunks_count: 25,
  },
  {
    id: 'c-104-sla-datacenter',
    organization_id: 'org-demo-lexflow',
    created_by_id: 'usr-1',
    title: 'Service Level Agreement (Equinix Colocation)',
    description: 'Tier-4 datacenter uptime, network availability guarantees, and power redundancy terms.',
    contract_type: 'sla',
    status: 'active',
    file_hash: 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35',
    file_size_bytes: 890000,
    effective_date: '2025-11-01',
    expiration_date: '2026-10-31',
    metadata_json: {
      source_type: 'pdf',
      page_count: 5,
      total_characters: 11200,
      total_chunks: 12,
      original_filename: 'Equinix_SLA_Colo_2025.pdf',
      content_type: 'application/pdf',
    },
    created_at: '2025-11-01T08:00:00Z',
    updated_at: '2025-11-01T08:00:00Z',
    document_chunks_count: 12,
  },
  {
    id: 'c-105-vendor-sap',
    organization_id: 'org-demo-lexflow',
    created_by_id: 'usr-3',
    title: 'Software License & Subscription Agreement (SAP ERP)',
    description: 'Enterprise ERP licensing schedule, database seats, and annual maintenance terms.',
    contract_type: 'vendor',
    status: 'draft',
    file_hash: '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce',
    file_size_bytes: 3200100,
    effective_date: '2026-05-01',
    expiration_date: '2029-04-30',
    metadata_json: {
      source_type: 'docx',
      page_count: 18,
      total_characters: 38900,
      total_chunks: 39,
      original_filename: 'SAP_Enterprise_Subscription_Draft.docx',
      content_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    },
    created_at: '2026-03-15T15:20:00Z',
    updated_at: '2026-03-15T15:20:00Z',
    document_chunks_count: 39,
  }
];

export const DEMO_CLAUSES: Clause[] = [
  {
    id: 'cl-1',
    contract_id: 'c-101-msa-apex',
    clause_type: 'limitation_of_liability',
    title: 'Limitation of Liability & Consequential Damages Waiver',
    text: 'NEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL OR PUNITIVE DAMAGES. EXCEPT FOR INDEMNIFICATION OBLIGATIONS, TOTAL AGGREGATE LIABILITY SHALL NOT EXCEED THE TOTAL FEES PAID HEREUNDER IN THE PRECEDING TWELVE (12) MONTHS.',
    risk_level: 'critical',
    page_number: 6,
    rule_match_indicator: 0.94,
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'cl-2',
    contract_id: 'c-101-msa-apex',
    clause_type: 'indemnification',
    title: 'Intellectual Property & Third-Party Indemnification',
    text: 'Vendor shall defend, indemnify, and hold harmless Customer, its officers, and employees against any and all third-party claims, suits, or proceedings alleging that the deliverables infringe any valid copyright or trade secret.',
    risk_level: 'high',
    page_number: 5,
    rule_match_indicator: 0.88,
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'cl-3',
    contract_id: 'c-101-msa-apex',
    clause_type: 'termination',
    title: 'Termination for Cause and Convenience',
    text: 'Customer may terminate this Agreement without cause upon providing sixty (60) days prior written notice. Either party may terminate immediately upon written notice if the other party breaches any material term and fails to cure within thirty (30) days.',
    risk_level: 'medium',
    page_number: 4,
    rule_match_indicator: 0.91,
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'cl-4',
    contract_id: 'c-101-msa-apex',
    clause_type: 'payment_terms',
    title: 'Invoicing & Net 30 Payment Terms',
    text: 'Vendor shall submit monthly invoices for services rendered. Customer shall remit payment within thirty (30) days of receipt of a valid and undisputed invoice via electronic wire transfer.',
    risk_level: 'low',
    page_number: 3,
    rule_match_indicator: 0.96,
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'cl-5',
    contract_id: 'c-101-msa-apex',
    clause_type: 'governing_law',
    title: 'Governing Law and Jurisdiction',
    text: 'This Agreement shall be governed by, and construed in accordance with, the laws of the State of Delaware, without giving effect to conflicts of law principles.',
    risk_level: 'low',
    page_number: 8,
    rule_match_indicator: 0.99,
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'cl-6',
    contract_id: 'c-101-msa-apex',
    clause_type: 'confidentiality',
    title: 'Nondisclosure and Non-Use of Confidential Information',
    text: 'Each party agrees to safeguard the Confidential Information of the other party with the same degree of care it uses for its own proprietary information of like nature, but not less than reasonable care.',
    risk_level: 'low',
    page_number: 4,
    rule_match_indicator: 0.92,
    created_at: '2026-01-16T14:20:00Z'
  }
];

export const DEMO_RISKS: RiskAssessment[] = [
  {
    id: 'risk-1',
    contract_id: 'c-101-msa-apex',
    rule_id: 'RULE-LIAB-02',
    title: 'Uncapped Liability Exposure in Indemnification Carve-out',
    severity: 'critical',
    risk_score: 10.0,
    category: 'Financial',
    description: 'Indemnification obligations are explicitly carved out from the 12-month aggregate fee liability cap, creating open-ended financial risk in the event of third-party IP lawsuits.',
    evidence_text: 'EXCEPT FOR INDEMNIFICATION OBLIGATIONS, TOTAL AGGREGATE LIABILITY SHALL NOT EXCEED THE TOTAL FEES PAID HEREUNDER...',
    mitigation_strategy: 'Negotiate a super-cap (e.g., 2x to 3x annual fees) on indemnification liabilities rather than leaving indemnity completely uncapped.',
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'risk-2',
    contract_id: 'c-101-msa-apex',
    rule_id: 'RULE-TERM-02',
    title: 'Unilateral Customer Termination for Convenience',
    severity: 'high',
    risk_score: 7.0,
    category: 'Operational',
    description: 'Contract grants Customer the right to cancel without cause upon 60 days notice with no early termination fee or recoupment for unamortized onboarding costs.',
    evidence_text: 'Customer may terminate this Agreement without cause upon providing sixty (60) days prior written notice.',
    mitigation_strategy: 'Insert reciprocal termination for convenience or require Customer to reimburse non-recoverable capital investments upon early termination.',
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'risk-3',
    contract_id: 'c-101-msa-apex',
    rule_id: 'RULE-RNW-01',
    title: 'Automatic Evergreen Renewal Without Explicit Notice Window',
    severity: 'medium',
    risk_score: 4.0,
    category: 'Operational',
    description: 'Schedule Section 3.2 indicates contract renews automatically for successive 1-year terms without specifying a 30-day opt-out window.',
    evidence_text: '...this Agreement shall automatically renew for successive one (1) year periods unless written notice is received prior to expiration.',
    mitigation_strategy: 'Define clear 45-day prior written notice requirement for non-renewal to prevent unwanted rollover.',
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'risk-4',
    contract_id: 'c-103-dpa-cloud',
    rule_id: 'RULE-DISP-01',
    title: 'Missing Arbitration & Mediation Escalation Clauses',
    severity: 'low',
    risk_score: 1.0,
    category: 'Legal',
    description: 'Document lacks a structured multi-tiered dispute escalation procedure before court filings.',
    evidence_text: 'No formal dispute resolution procedure detected.',
    mitigation_strategy: 'Incorporate standard 30-day executive mediation followed by binding AAA arbitration.',
    created_at: '2026-03-11T16:00:00Z'
  }
];

export const DEMO_OBLIGATIONS: Obligation[] = [
  {
    id: 'ob-1',
    contract_id: 'c-101-msa-apex',
    contract_title: 'Master Services Agreement (Apex Global Systems)',
    title: 'Annual SOC 2 Type II Compliance Report Delivery',
    responsible_party: 'Vendor (Apex)',
    due_date: '2026-04-30',
    deadline_type: 'exact',
    frequency: 'annual',
    status: 'pending',
    priority: 'high',
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'ob-2',
    contract_id: 'c-101-msa-apex',
    contract_title: 'Master Services Agreement (Apex Global Systems)',
    title: 'Monthly Uptime Availability Reporting & SLA Rebate Calculation',
    responsible_party: 'Vendor (Apex)',
    due_date: '2026-04-05',
    deadline_type: 'relative',
    relative_deadline_text: 'Within 5 business days following month-end',
    frequency: 'monthly',
    status: 'in_progress',
    priority: 'medium',
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'ob-3',
    contract_id: 'c-101-msa-apex',
    contract_title: 'Master Services Agreement (Apex Global Systems)',
    title: 'Remit Monthly Infrastructure Service Fees (Net 30)',
    responsible_party: 'Client / Customer',
    due_date: '2026-04-15',
    deadline_type: 'exact',
    frequency: 'monthly',
    status: 'pending',
    priority: 'medium',
    created_at: '2026-01-16T14:20:00Z'
  },
  {
    id: 'ob-4',
    contract_id: 'c-102-nda-zenith',
    contract_title: 'Mutual Non-Disclosure Agreement (Zenith BioTech)',
    title: 'Return or Certify Destruction of Confidential Research Materials',
    responsible_party: 'Each Party',
    due_date: '2028-02-15',
    deadline_type: 'relative',
    relative_deadline_text: 'Within 14 days of written demand or agreement termination',
    frequency: 'one_time',
    status: 'pending',
    priority: 'high',
    created_at: '2026-02-01T09:15:00Z'
  },
  {
    id: 'ob-5',
    contract_id: 'c-103-dpa-cloud',
    contract_title: 'Data Processing Addendum (CloudScale AI Europe)',
    title: 'Notice of Security Incident / Personal Data Breach within 48 Hours',
    responsible_party: 'Data Processor (CloudScale)',
    due_date: '2026-03-20',
    deadline_type: 'relative',
    relative_deadline_text: 'Without undue delay and not later than 48 hours following discovery',
    frequency: 'one_time',
    status: 'breached',
    priority: 'critical',
    created_at: '2026-03-11T16:00:00Z'
  }
];

export const DEMO_CONTROLS: ComplianceControl[] = [
  {
    id: 'ctl-101',
    organization_id: 'org-demo-lexflow',
    control_code: 'CTL-SOC2-CC6.1',
    name: 'Logical Access & Multi-Tenant Authorization Enforcement',
    description: 'Requires all contract data and analysis records to be protected by tenant-scoped cryptographic access boundaries.',
    category: 'Security',
    framework: 'SOC2',
    requirement: 'Enforce strict organization-level isolation and RBAC authorization across all endpoints.',
    status: 'active',
    tasks_count: 3,
    created_at: '2026-01-10T12:00:00Z',
    updated_at: '2026-01-10T12:00:00Z'
  },
  {
    id: 'ctl-102',
    organization_id: 'org-demo-lexflow',
    control_code: 'CTL-GDPR-ART28',
    name: 'Processor Agreement & Standard Contractual Clauses (SCCs)',
    description: 'Mandates formal DPA execution with all cloud sub-processors handling EU citizen data.',
    category: 'Privacy',
    framework: 'GDPR',
    requirement: 'Maintain active and legally verified Data Processing Addenda with all vendors.',
    status: 'active',
    tasks_count: 2,
    created_at: '2026-01-12T15:00:00Z',
    updated_at: '2026-01-12T15:00:00Z'
  },
  {
    id: 'ctl-103',
    organization_id: 'org-demo-lexflow',
    control_code: 'CTL-ISO-A.12.4',
    name: 'Security Audit Logging & Immutable Record Retention',
    description: 'Captures and retains structured JSON event details for all file uploads, viewing, deletions, and user logins.',
    category: 'Audit & Compliance',
    framework: 'ISO27001',
    requirement: 'Log every privileged action and store non-repudiable audit trails for minimum 365 days.',
    status: 'active',
    tasks_count: 1,
    created_at: '2026-01-15T09:30:00Z',
    updated_at: '2026-01-15T09:30:00Z'
  },
  {
    id: 'ctl-104',
    organization_id: 'org-demo-lexflow',
    control_code: 'CTL-HIPAA-SEC164',
    name: 'Business Associate Agreement (BAA) Verification',
    description: 'Ensures healthcare integrations have signed BAA provisions before PHI ingestion.',
    category: 'Healthcare',
    framework: 'HIPAA',
    requirement: 'Execute BAA before transmitting or processing protected health information.',
    status: 'inactive',
    tasks_count: 0,
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z'
  }
];

export const DEMO_TASKS: ComplianceTask[] = [
  {
    id: 'tsk-201',
    organization_id: 'org-demo-lexflow',
    control_id: 'ctl-101',
    control_code: 'CTL-SOC2-CC6.1',
    control_name: 'Logical Access & Multi-Tenant Authorization Enforcement',
    contract_id: 'c-101-msa-apex',
    contract_title: 'Master Services Agreement (Apex Global Systems)',
    obligation_id: 'ob-1',
    assignee_name: 'Alexander Hamilton',
    assigned_to_id: 'usr-1',
    title: 'Audit Apex Global Annual SOC 2 Type II Vendor Attestation',
    description: 'Review third-party auditor report and check for qualified opinion carve-outs.',
    status: 'in_progress',
    priority: 'high',
    due_date: '2026-04-30',
    created_at: '2026-01-20T10:00:00Z',
    updated_at: '2026-01-25T11:00:00Z'
  },
  {
    id: 'tsk-202',
    organization_id: 'org-demo-lexflow',
    control_id: 'ctl-102',
    control_code: 'CTL-GDPR-ART28',
    contract_id: 'c-103-dpa-cloud',
    contract_title: 'Data Processing Addendum (CloudScale AI Europe)',
    obligation_id: 'ob-5',
    assignee_name: 'Elena Rostova',
    assigned_to_id: 'usr-2',
    title: 'Execute EU Standard Contractual Clauses (Module 2 Controller-to-Processor)',
    description: 'Verify sub-processor list and execute Annex 1 transfer description.',
    status: 'pending',
    priority: 'critical',
    due_date: '2026-04-10',
    created_at: '2026-03-12T08:30:00Z',
    updated_at: '2026-03-12T08:30:00Z'
  },
  {
    id: 'tsk-203',
    organization_id: 'org-demo-lexflow',
    control_id: 'ctl-103',
    control_code: 'CTL-ISO-A.12.4',
    contract_id: 'c-104-sla-datacenter',
    contract_title: 'Service Level Agreement (Equinix Colocation)',
    assignee_name: 'Marcus Vance',
    assigned_to_id: 'usr-3',
    title: 'Quarterly Audit Log Archival & Integrity Verification',
    description: 'Verify SHA-256 hash chains on cold storage security logs.',
    status: 'completed',
    priority: 'medium',
    due_date: '2026-03-01',
    completed_at: '2026-02-28T16:45:00Z',
    created_at: '2026-01-05T09:00:00Z',
    updated_at: '2026-02-28T16:45:00Z'
  },
  {
    id: 'tsk-204',
    organization_id: 'org-demo-lexflow',
    control_id: 'ctl-101',
    control_code: 'CTL-SOC2-CC6.1',
    contract_id: 'c-105-vendor-sap',
    contract_title: 'Software License & Subscription Agreement (SAP ERP)',
    assignee_name: 'Alexander Hamilton',
    assigned_to_id: 'usr-1',
    title: 'Remediate Uncapped Indemnification Terms in SAP Draft',
    description: 'Schedule legal redline meeting with vendor counsel to cap IP infringement exposure.',
    status: 'overdue',
    priority: 'critical',
    due_date: '2026-03-20',
    created_at: '2026-03-10T14:00:00Z',
    updated_at: '2026-03-24T18:00:00Z'
  }
];

export const DEMO_DASHBOARD: ComplianceDashboard = {
  total_tasks: 4,
  pending_tasks: 1,
  in_progress_tasks: 1,
  completed_tasks: 1,
  overdue_tasks: 1,
  tasks_by_priority: {
    critical: 2,
    high: 1,
    medium: 1,
    low: 0,
  },
  tasks_due_next_7_days: 1,
  compliance_controls_count: 3,
  completion_percentage: 25.0,
};

export const DEMO_AUDIT_LOGS: AuditLog[] = [
  {
    id: 'aud-901',
    organization_id: 'org-demo-lexflow',
    user_id: 'usr-1',
    user_name: 'Alexander Hamilton',
    action: 'CONTRACT_UPLOADED',
    entity_type: 'contract',
    entity_id: 'c-101-msa-apex',
    details: {
      filename: 'Apex_Global_MSA_2026.pdf',
      filesize_bytes: 2458900,
      format: 'pdf',
      chunks_generated: 19
    },
    ip_address: '192.168.1.104',
    created_at: '2026-03-24T17:45:12Z'
  },
  {
    id: 'aud-902',
    organization_id: 'org-demo-lexflow',
    user_id: 'usr-1',
    user_name: 'Alexander Hamilton',
    action: 'CONTRACT_ANALYZED',
    entity_type: 'contract',
    entity_id: 'c-101-msa-apex',
    details: {
      clauses_detected: 6,
      risks_flagged: 3,
      overall_risk_score: 21.0,
      risk_band: 'Medium'
    },
    ip_address: '192.168.1.104',
    created_at: '2026-03-24T17:46:01Z'
  },
  {
    id: 'aud-903',
    organization_id: 'org-demo-lexflow',
    user_id: 'usr-2',
    user_name: 'Elena Rostova',
    action: 'COMPLIANCE_TASK_CREATED',
    entity_type: 'compliance_task',
    entity_id: 'tsk-202',
    details: {
      title: 'Execute EU Standard Contractual Clauses',
      priority: 'critical',
      due_date: '2026-04-10'
    },
    ip_address: '10.0.4.88',
    created_at: '2026-03-24T16:20:30Z'
  },
  {
    id: 'aud-904',
    organization_id: 'org-demo-lexflow',
    user_id: 'usr-3',
    user_name: 'Marcus Vance',
    action: 'COMPLIANCE_TASK_COMPLETED',
    entity_type: 'compliance_task',
    entity_id: 'tsk-203',
    details: {
      task_id: 'tsk-203',
      completion_time: '2026-02-28T16:45:00Z'
    },
    ip_address: '10.0.2.14',
    created_at: '2026-03-24T15:10:05Z'
  },
  {
    id: 'aud-905',
    organization_id: 'org-demo-lexflow',
    user_id: 'usr-1',
    user_name: 'Alexander Hamilton',
    action: 'USER_LOGIN',
    entity_type: 'user',
    entity_id: 'usr-1',
    details: {
      email: 'alexander@hamiltonlegal.com',
      auth_method: 'argon2_jwt'
    },
    ip_address: '192.168.1.104',
    created_at: '2026-03-24T14:02:11Z'
  }
];

export const DEMO_SEARCH_PASSAGES: SearchResultPassage[] = [
  {
    id: 'pass-1',
    contract_id: 'c-101-msa-apex',
    contract_title: 'Master Services Agreement (Apex Global Systems)',
    contract_type: 'msa',
    chunk_index: 5,
    page_number: 6,
    matched_clause_type: 'Limitation of Liability',
    snippet: '...EXCEPT FOR INDEMNIFICATION OBLIGATIONS UNDER SECTION 8, TOTAL AGGREGATE LIABILITY OF EITHER PARTY SHALL NOT EXCEED THE TOTAL FEES PAID HEREUNDER IN THE PRECEDING TWELVE (12) MONTHS. NEITHER PARTY SHALL BE LIABLE FOR LOST PROFITS OR CONSEQUENTIAL DAMAGES...',
    exact_match_score: 0.96,
    responsible_party: 'Both Parties'
  },
  {
    id: 'pass-2',
    contract_id: 'c-101-msa-apex',
    contract_title: 'Master Services Agreement (Apex Global Systems)',
    contract_type: 'msa',
    chunk_index: 4,
    page_number: 5,
    matched_clause_type: 'Indemnification',
    snippet: '...Vendor shall defend, indemnify, and hold harmless Customer, its officers, directors, and employees against any third-party claims alleging that the software infringes any United States patent, copyright, or trade secret...',
    exact_match_score: 0.91,
    responsible_party: 'Vendor (Apex)'
  },
  {
    id: 'pass-3',
    contract_id: 'c-103-dpa-cloud',
    contract_title: 'Data Processing Addendum (CloudScale AI Europe)',
    contract_type: 'dpa',
    chunk_index: 11,
    page_number: 4,
    matched_clause_type: 'Data Protection & Security Breach',
    snippet: '...In the event of a confirmed Personal Data Breach, Data Processor shall notify Data Controller without undue delay and in any event within forty-eight (48) hours after becoming aware of such incident...',
    exact_match_score: 0.89,
    responsible_party: 'Data Processor (CloudScale)'
  },
  {
    id: 'pass-4',
    contract_id: 'c-102-nda-zenith',
    contract_title: 'Mutual Non-Disclosure Agreement (Zenith BioTech)',
    contract_type: 'nda',
    chunk_index: 2,
    page_number: 2,
    matched_clause_type: 'Confidentiality',
    snippet: '...Recipient agrees that it shall protect Discloser’s Confidential Information with the same degree of care, but not less than a reasonable degree of care, that Recipient uses to protect its own confidential information of like nature...',
    exact_match_score: 0.85,
    responsible_party: 'Each Party'
  }
];
