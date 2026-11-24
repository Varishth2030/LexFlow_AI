import uuid
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import (
    AuditAction,
    AuditLog,
    Clause,
    ClauseType,
    ComplianceControl,
    ComplianceTask,
    Contract,
    ContractStatus,
    ContractType,
    ControlFramework,
    ControlStatus,
    DocumentChunk,
    Obligation,
    ObligationFrequency,
    ObligationStatus,
    Organization,
    RiskAssessment,
    RiskCategory,
    RiskSeverity,
    RiskStatus,
    TaskPriority,
    TaskStatus,
    User,
    UserRole,
)


def test_create_organization(db_session):
    """
    Test creating an organization with UUID and timestamps.
    """
    org = Organization(
        name="Acme Legal Corp",
        slug="acme-legal",
        is_active=True,
    )
    db_session.add(org)
    db_session.flush()

    assert isinstance(org.id, uuid.UUID)
    assert org.name == "Acme Legal Corp"
    assert org.slug == "acme-legal"
    assert org.is_active is True
    assert isinstance(org.created_at, datetime)
    assert isinstance(org.updated_at, datetime)


def test_organization_unique_slug_constraint(db_session):
    """
    Verify slug uniqueness constraint raises IntegrityError on collision.
    """
    org1 = Organization(name="Org One", slug="duplicate-slug")
    db_session.add(org1)
    db_session.flush()

    org2 = Organization(name="Org Two", slug="duplicate-slug")
    db_session.add(org2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_create_user_and_relationship(db_session):
    """
    Test user creation, foreign key to organization, and relationship back-population.
    """
    org = Organization(name="Lex Corp", slug="lex-corp")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email="counsel@lexcorp.com",
        full_name="Sarah Connor",
        hashed_password="secure_hashed_password_123",
        role=UserRole.ADMIN.value,
    )
    db_session.add(user)
    db_session.flush()

    assert isinstance(user.id, uuid.UUID)
    assert user.organization_id == org.id
    assert user.organization.name == "Lex Corp"
    assert user in org.users


def test_user_email_uniqueness(db_session):
    """
    Verify user email uniqueness constraint.
    """
    org = Organization(name="Org A", slug="org-a")
    db_session.add(org)
    db_session.flush()

    u1 = User(
        organization_id=org.id,
        email="duplicate@example.com",
        full_name="User One",
        hashed_password="hash1",
    )
    db_session.add(u1)
    db_session.flush()

    u2 = User(
        organization_id=org.id,
        email="duplicate@example.com",
        full_name="User Two",
        hashed_password="hash2",
    )
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_create_contract_and_creator(db_session):
    """
    Test contract creation, linking to organization and creator user.
    """
    org = Organization(name="TechCorp", slug="techcorp")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email="lawyer@techcorp.com",
        full_name="Harvey Specter",
        hashed_password="hash",
    )
    db_session.add(user)
    db_session.flush()

    contract = Contract(
        organization_id=org.id,
        created_by_id=user.id,
        title="Master Services Agreement 2026",
        description="Vendor contract for IT infrastructure",
        contract_type=ContractType.MSA.value,
        status=ContractStatus.ACTIVE.value,
        effective_date=date(2026, 1, 1),
        expiration_date=date(2027, 1, 1),
        metadata_json={"contract_value_usd": 150000, "jurisdiction": "Delaware"},
    )
    db_session.add(contract)
    db_session.flush()

    assert isinstance(contract.id, uuid.UUID)
    assert contract.creator == user
    assert contract in org.contracts
    assert contract in user.created_contracts
    assert contract.metadata_json["contract_value_usd"] == 150000


def test_create_document_chunk(db_session):
    """
    Test document chunk creation for RAG vector search preparation.
    """
    org = Organization(name="DocOrg", slug="doc-org")
    db_session.add(org)
    db_session.flush()

    contract = Contract(
        organization_id=org.id,
        title="Software License Agreement",
    )
    db_session.add(contract)
    db_session.flush()

    chunk = DocumentChunk(
        contract_id=contract.id,
        organization_id=org.id,
        chunk_index=0,
        content="This Agreement is entered into by and between...",
        token_count=120,
        page_number=1,
        embedding_metadata={"chunk_hash": "abc123hash"},
    )
    db_session.add(chunk)
    db_session.flush()

    assert chunk.contract == contract
    assert chunk in contract.document_chunks
    assert chunk.embedding_metadata["chunk_hash"] == "abc123hash"


def test_create_clause_risk_and_obligation(db_session):
    """
    Test clause creation along with child risk assessment and obligation.
    """
    org = Organization(name="Enterprise Legal", slug="ent-legal")
    db_session.add(org)
    db_session.flush()

    contract = Contract(
        organization_id=org.id,
        title="Cloud Vendor Agreement",
        contract_type=ContractType.VENDOR.value,
    )
    db_session.add(contract)
    db_session.flush()

    clause = Clause(
        contract_id=contract.id,
        organization_id=org.id,
        clause_type=ClauseType.LIMITATION_OF_LIABILITY.value,
        title="Limitation of Liability",
        text="In no event shall aggregate liability exceed 12 months fees paid...",
        page_number=8,
        risk_level=RiskSeverity.HIGH.value,
    )
    db_session.add(clause)
    db_session.flush()

    risk = RiskAssessment(
        contract_id=contract.id,
        organization_id=org.id,
        clause_id=clause.id,
        title="Uncapped IP Indemnity Exception",
        description="Liability cap carves out intellectual property indemnity.",
        risk_score=85.0,
        severity=RiskSeverity.HIGH.value,
        category=RiskCategory.LEGAL.value,
        mitigation_strategy="Request mutual sub-cap of 2x total contract value.",
        status=RiskStatus.IDENTIFIED.value,
    )
    db_session.add(risk)

    obligation = Obligation(
        contract_id=contract.id,
        organization_id=org.id,
        clause_id=clause.id,
        title="Annual SOC2 Report Delivery",
        description="Vendor must deliver SOC2 Type II report annually.",
        responsible_party="Vendor Inc.",
        due_date=date(2026, 12, 31),
        frequency=ObligationFrequency.RECURRING_ANNUAL.value,
        status=ObligationStatus.PENDING.value,
    )
    db_session.add(obligation)
    db_session.flush()

    assert clause in contract.clauses
    assert risk in contract.risk_assessments
    assert risk in clause.risk_assessments
    assert obligation in contract.obligations
    assert obligation in clause.obligations


def test_create_compliance_control_and_task(db_session):
    """
    Test compliance control, unique constraint on (org_id, code), and associated task.
    """
    org = Organization(name="Compliant Corp", slug="comp-corp")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email="compliance@compcorp.com",
        full_name="Auditor Alice",
        hashed_password="hash",
        role=UserRole.AUDITOR.value,
    )
    db_session.add(user)
    db_session.flush()

    control = ComplianceControl(
        organization_id=org.id,
        control_code="SOC2-CC6.1",
        name="Logical Access Controls",
        description="Access controls to prevent unauthorized data access.",
        framework=ControlFramework.SOC2.value,
        status=ControlStatus.ACTIVE.value,
    )
    db_session.add(control)
    db_session.flush()

    task = ComplianceTask(
        organization_id=org.id,
        control_id=control.id,
        assignee_id=user.id,
        title="Review Vendor Access Rights",
        description="Verify third-party access privileges are revoked after termination.",
        status=TaskStatus.IN_PROGRESS.value,
        priority=TaskPriority.HIGH.value,
        due_date=date(2026, 6, 30),
    )
    db_session.add(task)
    db_session.flush()

    assert task in control.compliance_tasks
    assert task.assignee == user
    assert task in user.assigned_tasks


def test_compliance_control_unique_code_per_org(db_session):
    """
    Test unique constraint (organization_id, control_code).
    """
    org = Organization(name="Security Co", slug="security-co")
    db_session.add(org)
    db_session.flush()

    c1 = ComplianceControl(
        organization_id=org.id,
        control_code="ISO-A5.1",
        name="Information Security Policies",
        description="Desc",
    )
    db_session.add(c1)
    db_session.flush()

    c2 = ComplianceControl(
        organization_id=org.id,
        control_code="ISO-A5.1",
        name="Duplicate Code",
        description="Desc",
    )
    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_audit_log_with_json_details(db_session):
    """
    Test audit log creation with structured JSON details dictionary.
    """
    org = Organization(name="Audit Org", slug="audit-org")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email="admin@auditorg.com",
        full_name="Admin User",
        hashed_password="hash",
    )
    db_session.add(user)
    db_session.flush()

    contract_id = uuid.uuid4()
    audit = AuditLog(
        organization_id=org.id,
        user_id=user.id,
        action=AuditAction.UPDATE.value,
        entity_type="Contract",
        entity_id=contract_id,
        details={
            "field_changed": "status",
            "old_value": "draft",
            "new_value": "active",
            "ip": "192.168.1.1",
        },
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 LexFlow Client",
    )
    db_session.add(audit)
    db_session.flush()

    assert isinstance(audit.id, uuid.UUID)
    assert audit.organization == org
    assert audit.user == user
    assert audit.details["field_changed"] == "status"
    assert audit.details["new_value"] == "active"


def test_foreign_key_enforcement(db_session):
    """
    Verify that foreign key constraints are strictly enforced in SQLite.
    Inserting a user with a non-existent organization_id must fail.
    """
    fake_org_id = uuid.uuid4()
    invalid_user = User(
        organization_id=fake_org_id,
        email="ghost@example.com",
        full_name="Ghost User",
        hashed_password="pw",
    )
    db_session.add(invalid_user)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_cascade_delete_organization(db_session):
    """
    Verify that deleting an organization cascades to delete all child entities.
    """
    org = Organization(name="Ephemeral Org", slug="ephemeral-org")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email="temp@ephemeral.com",
        full_name="Temp User",
        hashed_password="pw",
    )
    contract = Contract(organization_id=org.id, title="Temp Contract")
    db_session.add_all([user, contract])
    db_session.flush()

    user_id = user.id
    contract_id = contract.id

    # Delete organization
    db_session.delete(org)
    db_session.flush()

    # Verify children were cascaded
    deleted_user = db_session.execute(select(User).filter_by(id=user_id)).scalar_one_or_none()
    deleted_contract = db_session.execute(select(Contract).filter_by(id=contract_id)).scalar_one_or_none()

    assert deleted_user is None
    assert deleted_contract is None


def test_cascade_delete_contract(db_session):
    """
    Verify that deleting a contract cascades to delete clauses, chunks, risks, and obligations.
    """
    org = Organization(name="Parent Org", slug="parent-org")
    db_session.add(org)
    db_session.flush()

    contract = Contract(organization_id=org.id, title="Main Agreement")
    db_session.add(contract)
    db_session.flush()

    chunk = DocumentChunk(contract_id=contract.id, organization_id=org.id, chunk_index=0, content="Text")
    clause = Clause(contract_id=contract.id, organization_id=org.id, title="Confidentiality", text="NDA terms")
    db_session.add_all([chunk, clause])
    db_session.flush()

    risk = RiskAssessment(contract_id=contract.id, organization_id=org.id, clause_id=clause.id, title="Risk", description="Desc")
    obligation = Obligation(contract_id=contract.id, organization_id=org.id, clause_id=clause.id, title="Obligation", description="Desc", responsible_party="Party")
    db_session.add_all([risk, obligation])
    db_session.flush()

    chunk_id = chunk.id
    clause_id = clause.id
    risk_id = risk.id
    obligation_id = obligation.id

    db_session.delete(contract)
    db_session.flush()

    assert db_session.execute(select(DocumentChunk).filter_by(id=chunk_id)).scalar_one_or_none() is None
    assert db_session.execute(select(Clause).filter_by(id=clause_id)).scalar_one_or_none() is None
    assert db_session.execute(select(RiskAssessment).filter_by(id=risk_id)).scalar_one_or_none() is None
    assert db_session.execute(select(Obligation).filter_by(id=obligation_id)).scalar_one_or_none() is None


def test_organization_tenant_isolation(db_session):
    """
    Verify that query filtering by organization_id isolates tenant contracts.
    """
    org_a = Organization(name="Company A", slug="comp-a")
    org_b = Organization(name="Company B", slug="comp-b")
    db_session.add_all([org_a, org_b])
    db_session.flush()

    c_a = Contract(organization_id=org_a.id, title="Contract A1")
    c_b = Contract(organization_id=org_b.id, title="Contract B1")
    db_session.add_all([c_a, c_b])
    db_session.flush()

    # Query for Org A
    org_a_contracts = db_session.execute(
        select(Contract).filter_by(organization_id=org_a.id)
    ).scalars().all()

    assert len(org_a_contracts) == 1
    assert org_a_contracts[0].title == "Contract A1"
    assert c_b not in org_a_contracts
