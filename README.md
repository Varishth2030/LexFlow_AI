# LexFlow AI - Backend Foundation & Contract Processing

LexFlow AI is an AI-powered legal compliance and contract workflow intelligence platform. This repository contains the FastAPI backend, SQLAlchemy 2.0 ORM domain models, Alembic migrations, multi-tenant authentication/authorization engine, and document processing pipeline for PDF and DOCX contracts.

---

## 🛠 Tech Stack

- **Python 3.11**
- **FastAPI** (Modular REST API with auto-generated Swagger UI / OpenAPI)
- **SQLite 3.45.1** (Configured with `check_same_thread=False` and enforced foreign keys)
- **SQLAlchemy 2.0** (Mapped ORM declarations and relationship definitions)
- **Alembic** (Database migration management with batch mode for SQLite)
- **PyMuPDF 2.1** (Page-by-page PDF text extraction and metadata parsing)
- **python-docx 1.2.0** (Structured Word document paragraph and table text extraction)
- **pwdlib with Argon2id** (Cryptographically secure password hashing)
- **PyJWT** (HMAC-SHA256 signed JWT bearer tokens)
- **Pytest** (Comprehensive test suite with 172 passing automated unit, integration, security, search, reports, and tenant isolation tests)

---

## 🚀 Getting Started & Setup

### 1. Prerequisites
- Windows OS (or Linux/macOS)
- Python 3.11
- Existing virtual environment located in `backend/venv`

### 2. Activate the Virtual Environment
#### Windows (PowerShell)
```powershell
cd "backend"
.\venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt)
```cmd
cd backend
venv\Scripts\activate.bat
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` if not already present:
```powershell
Copy-Item .env.example .env
```
Key configuration parameters:
- `DATABASE_URL`: `sqlite:///./lexflow.db`
- `SECRET_KEY`: Minimum 32-character secret key used for signing JWT tokens.
- `ALGORITHM`: `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time in minutes (default: `1440` for 24h).
- `UPLOAD_DIR`: Target directory for contract files (default: `uploads`).
- `MAX_UPLOAD_SIZE_BYTES`: Maximum upload size in bytes (default: `15728640` for 15 MB).
- `BACKEND_CORS_ORIGINS`: Allowed frontend origins (React / Vite ports).

### 4. Run Database Migrations
Apply database schema migrations to SQLite:
```powershell
alembic upgrade head
```

### 5. Run the Development Server
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
The API will be available at:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 6. Run the Test Suite
```powershell
pytest -v
```
All **172 unit, integration, and security tests** will execute.

---

## 📄 Contract Upload & Document Processing (Milestone 4)

All contract processing endpoints are prefixed with `/api/v1/contracts` and require a valid Bearer JWT.

### Storage & Security Configuration
- **Max File Size**: 15 MB (configurable via `MAX_UPLOAD_SIZE_BYTES`).
- **Supported Formats**: `.pdf` and `.docx` only.
- **File Validation**: Multi-layer validation checking extension, MIME type, and binary magic bytes (`%PDF` for PDF, `PK\x03\x04` zip validation with `word/document.xml` for DOCX).
- **Anti-Path Traversal**: Filenames are randomized (`uuid.uuid4().hex + ext`) and stored in per-tenant folders (`uploads/{organization_id}/`). Original filenames are kept safely in database metadata.
- **Safe API Responses**: Internal filesystem paths (`file_path`) are never returned in API responses.
- **Privacy Assurance**: Documents are processed 100% locally using PyMuPDF and python-docx without sending any content to third-party or external AI APIs.

### Text Extraction & Chunking Strategy
- **PDF Extraction**:
  - Uses PyMuPDF (`pymupdf`).
  - Text extracted page by page, preserving 1-indexed `page_number`.
  - Empty or scanned PDFs without an embedded OCR text layer are detected and rejected.
- **DOCX Extraction**:
  - Uses python-docx.
  - Extracts both paragraph and table text with section references.
  - Preserves paragraph/table structure without inventing fake page numbers (`page_number: null`).
- **Document Chunking**:
  - Content is partitioned into sequential chunks (`chunk_index: 0, 1, 2, ...`) of up to 1000 characters along paragraph/sentence boundaries.
  - Each chunk is persisted in the `document_chunks` table linked to the contract and organization.

### Contract API Endpoints

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/contracts/upload` | Upload & Process Contract | Validates file, extracts text, chunks content, saves to disk, and records upload in DB and audit log. |
| `GET` | `/api/v1/contracts` | List Contracts | Paginated list (`skip`, `limit`) with text search (`search`) and type/status filters (`contract_type`, `status`). Strictly tenant-isolated. |
| `GET` | `/api/v1/contracts/{id}` | Get Contract Details | Retrieves contract metadata and all extracted document chunks. Returns 404 for other tenants. |
| `DELETE` | `/api/v1/contracts/{id}` | Delete Contract | Deletes contract, cascades chunk deletions, purges physical file from disk, and records audit log. |

#### Sample Contract Upload
`POST /api/v1/contracts/upload`  
*Headers:* `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`  
*Form fields:*
- `file`: `<binary file>`
- `title`: `Master Services Agreement 2026` *(optional)*
- `description`: `Vendor IT services contract` *(optional)*
- `contract_type`: `msa` *(optional)*

**Response (`201 Created`):**
```json
{
  "id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "organization_id": "8f12a345-678b-4cd2-8e34-567890abcdef",
  "created_by_id": "e4b6c312-789a-4bc1-9e23-456789abcdef",
  "title": "Master Services Agreement 2026",
  "description": "Vendor IT services contract",
  "contract_type": "msa",
  "status": "active",
  "file_hash": "a1b2c3d4e5f6...",
  "file_size_bytes": 102450,
  "effective_date": null,
  "expiration_date": null,
  "metadata_json": {
    "source_type": "pdf",
    "page_count": 5,
    "total_characters": 12450,
    "total_chunks": 14,
    "original_filename": "msa_2026.pdf",
    "content_type": "application/pdf"
  },
  "created_at": "2026-11-24T16:30:00Z",
  "updated_at": "2026-11-24T16:30:00Z",
  "document_chunks_count": 14,
  "document_chunks": [
    {
      "id": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",
      "contract_id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
      "chunk_index": 0,
      "content": "MASTER SERVICES AGREEMENT\nThis Agreement is entered into...",
      "token_count": 142,
      "page_number": 1,
      "embedding_metadata": {
        "source_type": "pdf",
        "page_number": 1,
        "char_count": 890,
        "word_count": 142
      },
      "created_at": "2026-11-24T16:30:00Z"
    }
  ]
}
```

---

## ⚖️ Rule-Based Contract Analysis Engine (Milestone 5)

Milestone 5 introduces a deterministic legal contract analysis engine engineered entirely in Python with zero external AI APIs, zero machine learning models, and zero LLM dependencies.

> [!IMPORTANT]
> **Zero LLM / Zero External API Architecture**:  
> LexFlow AI does NOT send contract data to OpenAI, Ollama, Anthropic, or any third-party AI provider. All analysis is performed deterministically, in-process, on local infrastructure.

### 1. Clause Detection (14 Categories)
Identifies and segments specific contractual provisions without classifying entire documents under a single label. Preserves document page numbers (for PDFs) and section indices (for DOCX):
1. **Payment Terms** (`payment_terms`)
2. **Termination** (`termination`)
3. **Confidentiality** (`confidentiality`)
4. **Indemnification** (`indemnification`)
5. **Limitation of Liability** (`limitation_of_liability`)
6. **Dispute Resolution** (`dispute_resolution`)
7. **Governing Law** (`governing_law`)
8. **Intellectual Property** (`intellectual_property`)
9. **Data Protection** (`data_protection`)
10. **Renewal** (`renewal`)
11. **Force Majeure** (`force_majeure`)
12. **Non-Compete** (`non_compete`)
13. **Warranty** (`warranty`)
14. **Delivery and Performance** (`delivery_and_performance`)

Each detected clause provides a deterministic `rule_match_indicator` (0.0 to 1.0) derived from regex heading patterns, body patterns, and keyword density.

### 2. Rule Catalogue & Risk Detection (12 Predefined Rules)

| Rule ID | Rule Name | Category | Severity | Detection Type | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `RULE-TERM-01` | Missing Termination Clause | Legal | High | Missing Clause | Flags agreements without exit provisions or breach cure terms. |
| `RULE-CONF-01` | Missing Confidentiality Clause | Legal | Medium | Missing Clause | Identifies unshielded exchange of proprietary or confidential information. |
| `RULE-LIAB-01` | Missing Limitation of Liability | Financial | Critical | Missing Clause | Highlights absent liability caps exposing the entity to uncapped damages. |
| `RULE-DISP-01` | Missing Dispute Resolution | Legal | Low | Missing Clause | Detects lack of structured negotiation, mediation, or arbitration mechanisms. |
| `RULE-GOV-01` | Missing Governing Law Clause | Legal | Low | Missing Clause | Identifies contracts lacking choice of law and venue jurisdiction clauses. |
| `RULE-LIAB-02` | Unlimited Liability Language | Financial | Critical | Pattern Match | Flags phrases like *"without limitation"*, *"no cap on liability"*, *"shall not be limited"*. |
| `RULE-TERM-02` | Unilateral Termination Rights | Operational | High | Pattern Match | Detects terms granting one party termination *"at its sole discretion"* or *"without cause"*. |
| `RULE-INDM-01` | Broad Indemnification Language | Legal | High | Pattern Match | Catches covenants to indemnify against *"any and all claims"* or *"howsoever arising"*. |
| `RULE-RNW-01` | Auto-Renewal Without Notice Window | Operational | Medium | Pattern Match | Flags evergreen clauses that renew automatically without a clear advance notice deadline. |
| `RULE-PAY-01` | Ambiguous Payment Deadlines | Financial | Medium | Pattern Match | Catches vague payment triggers like *"as soon as practicable"* or *"promptly upon receipt"*. |
| `RULE-IP-01` | Broad IP Assignment | Legal | High | Pattern Match | Identifies absolute assignments of *"all right, title, and interest"* or background IP. |
| `RULE-PEN-01` | Excessive Contractual Penalties | Financial | High | Pattern Match | Detects unenforceable punitive damages, penalty clauses, or immediate forfeiture. |

### 3. Transparent Risk Scoring Engine
- **Deterministic Weights**:
  - `Critical` = **10.0**
  - `High` = **7.0**
  - `Medium` = **4.0**
  - `Low` = **1.0**
- **Normalized Risk Bands**:
  - `0 - 9.9`: **Low**
  - `10.0 - 24.9`: **Medium**
  - `25.0 - 49.9`: **High**
  - `50.0+`: **Critical**
- **Legal Screening Disclaimer**: Included in every risk summary:
  > *"LexFlow AI provides deterministic, rule-based legal screening aids to highlight potential contractual risks and obligations. Outputs are not legal advice, binding conclusions, or a substitute for professional legal review by qualified counsel."*

### 4. Actionable Obligation & Deadline Extraction
- **Modal Verb Detection**: Extracts obligations using modal auxiliaries (`shall`, `must`, `agrees to`, `is required to`, `will be responsible for`, `undertakes to`, `covenants to`).
- **Party Attribution**: Identifies responsible actors (`Vendor`, `Client`, `Customer`, `Contractor`, `Company`, `Consultant`, `Each Party`, etc.) or marks `Unspecified (Needs Review)`.
- **Calendar Dates vs. Relative Deadlines**:
  - Parses explicit dates (`YYYY-MM-DD`, `Month DD, YYYY`, `DD/MM/YYYY`) into valid `date` objects.
  - Detects relative timeframes (`within 30 days`, `net 30`, `prior to effective date`) without fabricating or hallucinating calendar dates.

### 5. Contract Analysis API Endpoints

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/contracts/{id}/analyze` | Run Contract Analysis | Executes deterministic clause detection, risk rule evaluation, scoring, and obligation extraction. Idempotently updates DB and records audit log. |
| `GET` | `/api/v1/contracts/{id}/risks` | Get Contract Risks | Retrieves identified risks, severity counts, and overall risk band for a single contract. Supports `?severity=` filtering. |
| `GET` | `/api/v1/contracts/{id}/obligations` | Get Contract Obligations | Retrieves extracted obligations and deadlines for a single contract. Supports `?status=` and `?responsible_party=` filtering. |
| `GET` | `/api/v1/contracts/{id}/analysis` | Get Complete Analysis | Returns unified analysis record containing clauses, risks, obligations, score summary, and legal disclaimer. |
| `GET` | `/api/v1/contracts/risks` | List Org Risks (Milestone 8A) | Retrieves paginated risks across all contracts belonging to the authenticated tenant, with severity filter, score aggregates, and contract metadata. |
| `GET` | `/api/v1/contracts/obligations` | List Org Obligations (Milestone 8A) | Retrieves paginated obligations across all contracts belonging to the authenticated tenant, with status, due date, party filters, and contract metadata. |
| `POST` | `/api/v1/contracts/search` | Search Contract Passages (Milestone 8B) | Deterministic keyword and SQL pattern matching across stored document chunks with page citations, chunk index, clause attribution, and multi-tenant isolation. |

---

## 📋 Compliance Management Module (Milestone 6)

Milestone 6 adds a complete organization-scoped compliance management system with CRUD endpoints for controls and tasks, an aggregated dashboard, and automatic overdue detection.

### Compliance Controls

Compliance controls represent organizational policies, standards, or regulatory requirements. Each control is scoped to an organization and supports:
- **Control name**, **description**, **category**, and **requirement**.
- **Control code**: Auto-generated if omitted; unique per organization.
- **Status**: `active` or `inactive`.

### Compliance Tasks

Tasks link compliance controls to contracts, obligations, and assignees. Each task supports:
- **Title**, **description**, and **due date**.
- **Priority**: `low`, `medium`, `high`, or `critical`.
- **Status**: `pending`, `in_progress`, `completed`, or `overdue`.
- **Relations**: Optional links to a compliance control, contract, obligation, and assigned user.
- **Automatic overdue detection**: Tasks with a past due date that are not completed are dynamically marked `overdue` on retrieval.

### Compliance Dashboard

The dashboard endpoint aggregates real-time compliance metrics:
- Total tasks, pending, in progress, completed, and overdue counts.
- Task breakdown by priority level.
- Tasks due in the next 7 days.
- Total active controls and overall completion percentage.

### Compliance API Endpoints

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/compliance/controls` | List Controls | Paginated list with filtering by status, category, framework, and text search. |
| `POST` | `/api/v1/compliance/controls` | Create Control | Creates a new compliance control with auto-generated control code if omitted. |
| `GET` | `/api/v1/compliance/controls/{id}` | Get Control | Retrieves control details with associated task count. |
| `PATCH` | `/api/v1/compliance/controls/{id}` | Update Control | Partial update of control fields. |
| `DELETE` | `/api/v1/compliance/controls/{id}` | Delete Control | Deletes control and cascades to associated tasks. |
| `GET` | `/api/v1/compliance/tasks` | List Tasks | Paginated list with filtering by status, priority, due date, control, contract, and assignee. |
| `POST` | `/api/v1/compliance/tasks` | Create Task | Creates a task with validated relations (control, contract, obligation, assignee must belong to same org). |
| `GET` | `/api/v1/compliance/tasks/{id}` | Get Task | Retrieves task with dynamic overdue check. |
| `PATCH` | `/api/v1/compliance/tasks/{id}` | Update Task | Updates task fields; manages `completed_at` on status transitions. |
| `DELETE` | `/api/v1/compliance/tasks/{id}` | Delete Task | Deletes the task and records audit log. |
| `GET` | `/api/v1/compliance/dashboard` | Compliance Dashboard | Returns aggregated compliance metrics for the organization. |

### Audit Logging

All compliance CRUD operations, status transitions, and completions are recorded in the audit log with structured JSON event details.

---

## 🔍 Deterministic Contract Search & Audit Logging (Milestone 8B)

### 1. Deterministic Contract Search Engine
- **Endpoint**: `POST /api/v1/contracts/search`
- **Zero LLM / Zero Machine Learning**: Scans verbatim document chunks in SQLite using SQL pattern matching and keyword tokenization.
- **Citations & References**: Every search hit contains `contract_title`, `contract_type`, `contract_id`, `chunk_index`, `page_number`, `matched_clause_type`, `responsible_party`, and deterministic score.
- **Tenant Isolated**: Strictly filtered by `DocumentChunk.organization_id == current_user.organization_id`.
- **Mandatory Disclaimer**: Included in every response:
  > *"LexFlow AI deterministic search retrieves verbatim passages directly from stored document chunks. Results are not legal advice, binding conclusions, or AI-generated answers."*

### 2. Security & Compliance Audit Log API
- **Endpoint**: `GET /api/v1/audit`
- **Tenant Isolated**: Scoped strictly to `AuditLog.organization_id == current_user.organization_id`.
- **Joined User Actor**: Joins with `User` table to surface actor name (`user_name`) and email (`user_email`).
- **Filters & Pagination**: Supports filtering by `action` (CREATE, VIEW, UPDATE, DELETE, LOGIN), `entity_type`, `user_id`, `start_date`, `end_date`, `skip`, and `limit`.
- **Payload Inspection**: Structured event details preserved in JSON format for compliance inspection (ISO 27001 / SOC 2).

---

## 📊 Executive Reports & Analytics Export Engine (Milestone 9)

LexFlow AI includes an automated executive reporting and legal data export engine that aggregates portfolio-level metrics and produces auditable exports.

### 1. Executive Intelligence Summary API
- **Endpoint**: `GET /api/v1/reports/summary`
- **Portfolio Aggregation**: Computes active contract inventory, detected clauses count, overall risk register totals, obligation completion rates, and compliance control governance percentage.
- **Contract Type Breakdown**: Deterministic breakdown across NDA, MSA, Vendor, License, Service, and Employment agreements.
- **Quarterly Risk Trend**: Aggregates trailing 4 quarters of risk distribution by severity.

### 2. Multi-Format Data Exports
- **CSV Data Stream**: `GET /api/v1/reports/export/csv?type=executive|risks|obligations|compliance`
  - Streams formatted RFC 4180 CSV tables directly from SQLite records.
  - Generates audit log entry (`EXPORT`, `ReportCSV`) on every download.
- **Executive Dossier PDF**: `GET /api/v1/reports/export/pdf`
  - Uses PyMuPDF (`fitz`) to render multi-page corporate PDF dossiers with branded navy headers, metric highlight tiles, risk registers, and statutory legal disclaimers.
  - Zero external cloud services or rendering APIs used.

---

## 🏢 Enterprise Demo Seeding & Verification (Milestone 10)

The backend includes a fully idempotent demo data seeding script for immediate live demonstrations and evaluator inspection.

### Running the Seed Script
```powershell
cd backend
.\venv\Scripts\python.exe scripts\seed_demo_data.py
```

### Pre-Configured Enterprise Demo Account
- **Organization**: Hamilton Legal Group
- **Administrator Email**: `alexander@hamiltonlegal.com`
- **Password**: `SecurePassword2026!`
- **Pre-Loaded Records**:
  - 3 Processed Contracts (Enterprise Cloud MSA, Global Vendor NDA, SaaS License Agreement)
  - 11 Deterministically Evaluated Legal Risks (across Critical, High, Medium, Low bands)
  - 10 Extracted Contractual Obligations with mapped parties and due dates
  - 3 Active Compliance Controls (SOC 2 CC6.1, ISO 27001 A.12.1, GDPR Art. 32)
  - 4 Compliance Governance Tasks with status and priority tracking
  - Complete Security Audit Trail with immutable event logs

---

All authentication routes are prefixed with `/api/v1/auth`.

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register Organization & User | Atomically creates tenant organization and initial user with `owner` role. Hashes password via Argon2id. |
| `POST` | `/api/v1/auth/login` | User Login | Validates credentials and returns signed JWT access token containing `sub` (user_id) and `org_id` (organization_id). |
| `GET` | `/api/v1/auth/me` | Authenticated Profile | Returns current user profile and tenant organization context. |

---

## 🔑 How to Obtain & Use a Bearer Token in Swagger UI

1. Open your browser and navigate to **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.
2. Locate the **POST `/api/v1/auth/login`** endpoint:
   - Click **Try it out**.
   - Enter your registered `email` and `password`.
   - Click **Execute**.
3. In the response body, copy the value of `access_token` (without quotes).
4. Scroll to the top of Swagger UI and click the green **Authorize 🔓** button on the right.
5. In the **HTTPBearer (http, Bearer)** dialog:
   - Paste the token string into the **Value** input box.
   - Click **Authorize**.
   - Click **Close**.
6. The padlock icons will now appear locked 🔒. All subsequent requests executed through Swagger UI will automatically include the `Authorization: Bearer <access_token>` header.
7. Test it by expanding **GET `/api/v1/contracts`** or **POST `/api/v1/contracts/upload`** to test contract management.

---

## 🛡 Multi-Tenant Security & Isolation Model

- **No Client Spoofing**: Endpoints never trust client-supplied `organization_id` values in query parameters or request bodies.
- **Strict Token Derivation**: Tenant scope is derived exclusively from the authenticated user (`get_current_tenant_id` and `get_current_organization` dependencies in `app/api/deps.py`).
- **Cross-Organization Protection**: All contract queries, retrieval, and deletion endpoints strictly filter by `organization_id == current_user.organization_id`. Any attempt to access another organization's contract returns `404 Not Found`.
- **Relational Integrity**: Foreign key constraints are enforced on SQLite via connection pragmas. Cascade deletions clean up child records (chunks, clauses, risks, obligations) when an organization or contract is deleted.
- **Audit Logging**: Contract uploads, listings, views, and deletions are recorded in append-only audit records storing structured JSON event details.
