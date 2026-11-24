"""
LexFlow AI - Enterprise Demo Data Seeding Script (Milestone 10).
Populates an organization, admin user, realistic legal contracts, detected clauses,
risk assessments, extracted obligations, compliance controls, and audit logs.
"""

import io
import os
import sys
import uuid
import warnings
from datetime import date, datetime, timedelta, timezone

warnings.filterwarnings("ignore", category=FutureWarning)

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fitz  # PyMuPDF
from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models import (
    AuditAction,
    AuditLog,
    ComplianceControl,
    ComplianceTask,
    Contract,
    ContractStatus,
    ContractType,
    ControlFramework,
    ControlStatus,
    DocumentChunk,
    Organization,
    TaskPriority,
    TaskStatus,
    User,
    UserRole,
)
from app.services.contract_analyzer import analyze_contract


def generate_pdf_file(filepath: str, pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page(width=612, height=792)
        page.insert_text((54, 72), text, fontsize=10.5, fontname="helv")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc.save(filepath)
    doc.close()
    with open(filepath, "rb") as f:
        return f.read()


def seed_database():
    print("=" * 65)
    print("  LexFlow AI — Seeding Enterprise LegalTech Demo Database")
    print("=" * 65)

    db = SessionLocal()
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    os.makedirs(upload_dir, exist_ok=True)

    try:
        # 1. Organization
        org_slug = "hamilton-legal-group"
        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                name="Hamilton Legal Group",
                slug=org_slug,
                is_active=True,
            )
            db.add(org)
            db.flush()
            print(f"[✓] Created Organization: {org.name} ({org.id})")
        else:
            print(f"[i] Existing Organization: {org.name} ({org.id})")

        # 2. Administrator User
        user_email = "alexander@hamiltonlegal.com"
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                organization_id=org.id,
                email=user_email,
                full_name="Alexander Hamilton",
                hashed_password=get_password_hash("SecurePassword2026!"),
                role=UserRole.OWNER.value,
                is_active=True,
            )
            db.add(user)
            db.flush()
            print(f"[✓] Created Admin User: {user.email} (Password: SecurePassword2026!)")
        else:
            print(f"[i] Existing Admin User: {user.email}")

        # 3. Sample Contracts
        contracts_data = [
            {
                "title": "Enterprise Cloud Master Services Agreement (MSA)",
                "contract_type": ContractType.MSA.value,
                "filename": "Enterprise_Cloud_MSA.pdf",
                "pages": [
                    (
                        "MASTER SERVICES AGREEMENT\n\n"
                        "This Master Services Agreement ('Agreement') is entered into by and between CloudCore Inc. ('Vendor') "
                        "and Hamilton Legal Group ('Client').\n\n"
                        "1. Term and Termination.\n"
                        "This Agreement commences on the Effective Date and continues for an initial term of three (3) years. "
                        "Either party may terminate this Agreement for cause if the other party breaches any material term and "
                        "fails to cure such breach within thirty (30) days of receipt of written notice.\n\n"
                        "2. Payment Terms and Invoicing.\n"
                        "Vendor shall submit monthly invoices for Services rendered. Client shall pay all undisputed invoice amounts "
                        "within thirty (30) days of invoice receipt ('Net 30'). Late payments shall accrue interest at 1.5% per month.\n"
                    ),
                    (
                        "3. Confidentiality and Non-Disclosure.\n"
                        "Each Receiving Party agrees to protect the Confidential Information of the Disclosing Party using the same "
                        "degree of care it uses for its own proprietary information, but no less than reasonable care. Obligations "
                        "survive termination for a period of five (5) years.\n\n"
                        "4. Limitation of Liability and Damages.\n"
                        "IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES. "
                        "THE AGGREGATE LIABILITY OF EITHER PARTY SHALL NOT EXCEED THE TOTAL FEES PAID OR PAYABLE UNDER THIS AGREEMENT "
                        "IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM; PROVIDED HOWEVER, VENDOR LIABILITY FOR BREACH OF CONFIDENTIALITY "
                        "SHALL BE WITHOUT LIMITATION.\n\n"
                        "5. Indemnification.\n"
                        "Vendor shall defend, indemnify, and hold harmless Client against any third-party claim alleging intellectual "
                        "property infringement arising from authorized use of the Services.\n"
                    ),
                    (
                        "6. Data Protection and Security Compliance.\n"
                        "Vendor agrees to maintain SOC 2 Type II and ISO 27001 certifications throughout the term. Vendor shall notify "
                        "Client in writing within forty-eight (48) hours of becoming aware of any confirmed Personal Data breach.\n\n"
                        "7. Dispute Resolution and Governing Law.\n"
                        "This Agreement shall be governed by and construed in accordance with the laws of the State of New York. "
                        "Any dispute arising hereunder shall be submitted to binding arbitration in New York, NY."
                    ),
                ],
            },
            {
                "title": "Global Vendor Mutual Non-Disclosure Agreement",
                "contract_type": ContractType.NDA.value,
                "filename": "Global_Vendor_Mutual_NDA.pdf",
                "pages": [
                    (
                        "MUTUAL NON-DISCLOSURE AGREEMENT\n\n"
                        "This Mutual Non-Disclosure Agreement is entered into between Acme Solutions Ltd. and Hamilton Legal Group.\n\n"
                        "1. Scope of Confidentiality.\n"
                        "Confidential Information includes all technical, business, and financial data disclosed in connection with "
                        "evaluating potential joint commercial initiatives.\n\n"
                        "2. Obligations of Non-Use and Care.\n"
                        "Receiving Party shall not disclose proprietary information to third parties without prior written consent.\n\n"
                        "3. Term of Protection.\n"
                        "This Agreement shall remain in effect for two (2) years. The receiving party undertakes to return or "
                        "certify destruction of all confidential materials upon written request."
                    ),
                ],
            },
            {
                "title": "Software License & Support Agreement (SaaS)",
                "contract_type": ContractType.LICENSE.value,
                "filename": "Software_License_SaaS.pdf",
                "pages": [
                    (
                        "SOFTWARE LICENSE AND SUPPORT AGREEMENT\n\n"
                        "1. License Grant.\n"
                        "Licensor grants Licensee a non-exclusive, non-transferable enterprise subscription license.\n\n"
                        "2. Service Levels and Availability.\n"
                        "Licensor covenants that the platform will maintain 99.9% uptime during each calendar month.\n\n"
                        "3. Termination for Convenience.\n"
                        "Licensor may terminate this agreement at its sole discretion without cause upon five (5) days notice.\n\n"
                        "4. Evergreen Automatic Renewal.\n"
                        "This agreement shall renew automatically for successive 1-year terms unless notice of non-renewal is provided."
                    ),
                ],
            },
        ]

        created_contracts = []
        for cdata in contracts_data:
            existing = db.query(Contract).filter(
                Contract.organization_id == org.id,
                Contract.title == cdata["title"],
            ).first()

            if not existing:
                filepath = os.path.join(upload_dir, cdata["filename"])
                content = generate_pdf_file(filepath, cdata["pages"])

                contract = Contract(
                    id=uuid.uuid4(),
                    organization_id=org.id,
                    created_by_id=user.id,
                    title=cdata["title"],
                    description=f"Standard {cdata['contract_type'].upper()} contract for legal evaluation.",
                    contract_type=cdata["contract_type"],
                    status=ContractStatus.ACTIVE.value,
                    file_path=filepath,
                    file_hash=f"sha256_{uuid.uuid4().hex[:16]}",
                    file_size_bytes=len(content),
                    effective_date=date.today() - timedelta(days=60),
                    expiration_date=date.today() + timedelta(days=730),
                )
                db.add(contract)
                db.flush()

                # Document chunks
                for idx, page_text in enumerate(cdata["pages"]):
                    chunk = DocumentChunk(
                        id=uuid.uuid4(),
                        contract_id=contract.id,
                        organization_id=org.id,
                        chunk_index=idx,
                        content=page_text,
                        token_count=len(page_text.split()),
                        page_number=idx + 1,
                        embedding_metadata={"source_type": "pdf", "page": idx + 1},
                    )
                    db.add(chunk)
                # Commit contract + chunks before analysis (analyzer does its own commit)
                db.commit()

                # Run deterministic analysis engine
                analyze_contract(db, contract.id, user)
                created_contracts.append(contract)
                print(f"[✓] Created & Analyzed Contract: {contract.title}")
            else:
                created_contracts.append(existing)
                print(f"[i] Existing Contract: {existing.title}")

        # 4. Compliance Controls
        controls_data = [
            {
                "control_code": "CC6.1-ACCESS",
                "name": "Logical Access and Security Boundaries",
                "description": "Ensure multi-factor authentication, cryptographic tokens, and tenant isolation across all endpoints. SOC 2 Trust Services Criteria CC6.1.",
                "category": "Access Management",
                "framework": ControlFramework.SOC2.value,
                "status": ControlStatus.ACTIVE.value,
            },
            {
                "control_code": "ISO-A.12.1",
                "name": "Operational Security and Risk Management",
                "description": "Establish operational procedures and responsibilities to protect against contractual liabilities. ISO/IEC 27001:2022 Control A.12.1.",
                "category": "Operations",
                "framework": ControlFramework.ISO27001.value,
                "status": ControlStatus.ACTIVE.value,
            },
            {
                "control_code": "GDPR-ART.32",
                "name": "Technical and Organizational Security Measures",
                "description": "Enforce data encryption, breach notification windows, and contractual confidentiality protections. EU GDPR Article 32.",
                "category": "Data Protection",
                "framework": ControlFramework.GDPR.value,
                "status": ControlStatus.ACTIVE.value,
            },
        ]

        created_controls = []
        for ctl_data in controls_data:
            existing = db.query(ComplianceControl).filter(
                ComplianceControl.organization_id == org.id,
                ComplianceControl.control_code == ctl_data["control_code"],
            ).first()
            if not existing:
                ctrl = ComplianceControl(
                    id=uuid.uuid4(),
                    organization_id=org.id,
                    **ctl_data,
                )
                db.add(ctrl)
                db.flush()
                created_controls.append(ctrl)
                print(f"[✓] Created Compliance Control: {ctrl.control_code} - {ctrl.name}")
            else:
                created_controls.append(existing)
                print(f"[i] Existing Compliance Control: {existing.control_code}")

        # 5. Compliance Tasks
        tasks_data = [
            {
                "title": "Review Enterprise Cloud MSA Liability Redlines",
                "description": "Validate unlimited liability carve-outs with outside counsel before contract renewal.",
                "priority": TaskPriority.CRITICAL.value,
                "status": TaskStatus.COMPLETED.value,
                "due_date": date.today() - timedelta(days=5),
                "control_id": created_controls[0].id if created_controls else None,
                "contract_id": created_contracts[0].id if created_contracts else None,
            },
            {
                "title": "Obtain Annual SOC 2 Type II Attestation from CloudCore",
                "description": "Request and verify third-party security auditor attestation for cloud provider.",
                "priority": TaskPriority.HIGH.value,
                "status": TaskStatus.IN_PROGRESS.value,
                "due_date": date.today() + timedelta(days=14),
                "control_id": created_controls[0].id if created_controls else None,
                "contract_id": created_contracts[0].id if created_contracts else None,
            },
            {
                "title": "Review Sub-processor 48-Hour Breach Notification Protocol",
                "description": "Confirm vendor escalation paths comply with GDPR Art 32 and contractual DPA commitments.",
                "priority": TaskPriority.MEDIUM.value,
                "status": TaskStatus.PENDING.value,
                "due_date": date.today() + timedelta(days=30),
                "control_id": created_controls[2].id if len(created_controls) > 2 else None,
                "contract_id": created_contracts[0].id if created_contracts else None,
            },
            {
                "title": "Annual Non-Disclosure Agreement Registry Audit",
                "description": "Review expiring NDAs and issue retention/destruction confirmations.",
                "priority": TaskPriority.LOW.value,
                "status": TaskStatus.COMPLETED.value,
                "due_date": date.today() - timedelta(days=10),
                "control_id": created_controls[1].id if len(created_controls) > 1 else None,
                "contract_id": created_contracts[1].id if len(created_contracts) > 1 else None,
            },
        ]

        for tdata in tasks_data:
            existing = db.query(ComplianceTask).filter(
                ComplianceTask.organization_id == org.id,
                ComplianceTask.title == tdata["title"],
            ).first()
            if not existing:
                task = ComplianceTask(
                    id=uuid.uuid4(),
                    organization_id=org.id,
                    assignee_id=user.id,
                    **tdata,
                )
                db.add(task)
                db.flush()
                print(f"[✓] Created Compliance Task: {task.title} [{task.priority.upper()}]")
            else:
                print(f"[i] Existing Compliance Task: {existing.title}")

        # 6. Audit Trail Logs (idempotent: only seed if no logs exist for org)
        existing_logs_count = db.query(AuditLog).filter(AuditLog.organization_id == org.id).count()
        if existing_logs_count == 0:
            audit_events = [
                ("login", "User", user.id, {"event": "user_login_success", "email": user.email}),
                ("create", "Contract", created_contracts[0].id, {"event": "upload_contract", "title": created_contracts[0].title}),
                ("create", "ContractAnalysis", created_contracts[0].id, {"event": "analysis_engine_executed", "clauses": 6, "risks": 2}),
                ("create", "ComplianceControl", created_controls[0].id, {"event": "create_control", "code": created_controls[0].control_code}),
            ]
            for action, entity_type, entity_id, details in audit_events:
                audit = AuditLog(
                    id=uuid.uuid4(),
                    organization_id=org.id,
                    user_id=user.id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details,
                    ip_address="127.0.0.1",
                )
                db.add(audit)
            print("[✓] Created Initial Audit Trail Logs")
        else:
            print(f"[i] Existing Audit Trail ({existing_logs_count} events recorded)")

        db.commit()
        print("\n" + "=" * 65)
        print("  ✓ Database seeding successfully completed!")
        print(f"  Organization: {org.name}")
        print(f"  Login Email:  {user.email}")
        print("  Password:     SecurePassword2026!")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"[!] Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
