from enum import StrEnum


class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class ContractStatus(StrEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class ContractType(StrEnum):
    NDA = "nda"
    MSA = "msa"
    VENDOR = "vendor"
    EMPLOYMENT = "employment"
    SERVICE = "service"
    LICENSE = "license"
    OTHER = "other"


class ClauseType(StrEnum):
    PAYMENT_TERMS = "payment_terms"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INDEMNIFICATION = "indemnification"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    DISPUTE_RESOLUTION = "dispute_resolution"
    GOVERNING_LAW = "governing_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    DATA_PROTECTION = "data_protection"
    DATA_PRIVACY = "data_privacy"
    RENEWAL = "renewal"
    FORCE_MAJEURE = "force_majeure"
    NON_COMPETE = "non_compete"
    WARRANTY = "warranty"
    DELIVERY_AND_PERFORMANCE = "delivery_and_performance"
    GENERAL = "general"
    OTHER = "other"


class RiskSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(StrEnum):
    LEGAL = "legal"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    REPUTATIONAL = "reputational"
    OTHER = "other"


class RiskStatus(StrEnum):
    IDENTIFIED = "identified"
    UNDER_REVIEW = "under_review"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"


class ObligationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    WAIVED = "waived"


class ObligationFrequency(StrEnum):
    ONE_TIME = "one_time"
    RECURRING_MONTHLY = "recurring_monthly"
    RECURRING_QUARTERLY = "recurring_quarterly"
    RECURRING_ANNUAL = "recurring_annual"
    AS_NEEDED = "as_needed"


class ControlFramework(StrEnum):
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    NIST = "nist"
    INTERNAL = "internal"
    OTHER = "other"


class ControlStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class TaskStatus(StrEnum):
    PENDING = "pending"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    BLOCKED = "blocked"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
