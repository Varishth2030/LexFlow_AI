"""
LexFlow AI - Test Suite for Milestone 6: Compliance Management Module.

Comprehensive testing covering:
1. Compliance Control CRUD (create, read, update, delete).
2. Compliance Task CRUD with related entity validation.
3. Status transitions, priority validation, and due date handling.
4. Automatic overdue calculation.
5. Completed task handling (not marked overdue).
6. Filtering and pagination.
7. Dashboard statistics and completion percentage.
8. Audit log creation for all significant events.
9. Invalid related record IDs (control, contract, obligation, assignee).
10. Cross-organization access prevention.
11. Unauthorized (unauthenticated) access rejection.
"""

from datetime import date, timedelta
import uuid
import pytest

from app.models.enums import ControlFramework, ControlStatus, TaskPriority, TaskStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_a_headers(client):
    """Register & authenticate user for Organization A."""
    email = f"comp_a_{uuid.uuid4().hex[:6]}@lexflow.com"
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Compliance Officer A",
        "email": email,
        "password": "Password123!",
        "organization_name": f"CompFirm A {uuid.uuid4().hex[:4]}",
    })
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def org_b_headers(client):
    """Register & authenticate user for Organization B."""
    email = f"comp_b_{uuid.uuid4().hex[:6]}@lexflow.com"
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Compliance Officer B",
        "email": email,
        "password": "Password123!",
        "organization_name": f"CompFirm B {uuid.uuid4().hex[:4]}",
    })
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_control(client, headers, **overrides):
    """Helper to create a compliance control and return its JSON."""
    payload = {
        "name": overrides.get("name", "Access Control Policy"),
        "description": overrides.get("description", "Enforce logical access restrictions."),
        "category": overrides.get("category", "Access Management"),
        "framework": overrides.get("framework", "soc2"),
        "status": overrides.get("status", "active"),
    }
    if "control_code" in overrides:
        payload["control_code"] = overrides["control_code"]
    res = client.post("/api/v1/compliance/controls", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def _create_task(client, headers, **overrides):
    """Helper to create a compliance task and return its JSON."""
    payload = {
        "title": overrides.get("title", "Review access logs"),
        "description": overrides.get("description", "Audit access logs for Q4."),
        "priority": overrides.get("priority", "medium"),
        "status": overrides.get("status", "pending"),
    }
    for key in ("control_id", "contract_id", "obligation_id", "assignee_id", "assigned_to_id", "due_date"):
        if key in overrides:
            val = overrides[key]
            payload[key] = str(val) if isinstance(val, uuid.UUID) else val
    res = client.post("/api/v1/compliance/tasks", headers=headers, json=payload)
    return res


# ===========================================================================
# 1. COMPLIANCE CONTROL CRUD
# ===========================================================================

class TestComplianceControlCRUD:

    def test_create_control(self, client, org_a_headers):
        ctrl = _create_control(client, org_a_headers, name="Encryption Policy", control_code="SOC2-CC6.7")
        assert ctrl["name"] == "Encryption Policy"
        assert ctrl["control_code"] == "SOC2-CC6.7"
        assert ctrl["status"] == "active"
        assert ctrl["framework"] == "soc2"
        assert ctrl["id"] is not None

    def test_create_control_auto_code(self, client, org_a_headers):
        """Control code is auto-generated when omitted."""
        ctrl = _create_control(client, org_a_headers, name="Data Retention")
        assert ctrl["control_code"].startswith("CTRL-")

    def test_create_duplicate_code_rejected(self, client, org_a_headers):
        _create_control(client, org_a_headers, control_code="DUP-001")
        res = client.post("/api/v1/compliance/controls", headers=org_a_headers, json={
            "name": "Duplicate", "description": "Test", "control_code": "DUP-001",
        })
        assert res.status_code == 400
        assert "already exists" in res.json()["detail"]

    def test_list_controls(self, client, org_a_headers):
        _create_control(client, org_a_headers, name="Ctrl List 1", control_code="LIST-001")
        _create_control(client, org_a_headers, name="Ctrl List 2", control_code="LIST-002")
        res = client.get("/api/v1/compliance/controls", headers=org_a_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_list_controls_with_filter(self, client, org_a_headers):
        _create_control(client, org_a_headers, name="GDPR Data Map", framework="gdpr", control_code="GDPR-F1")
        res = client.get("/api/v1/compliance/controls?framework=gdpr", headers=org_a_headers)
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["framework"] == "gdpr"

    def test_get_control_by_id(self, client, org_a_headers):
        ctrl = _create_control(client, org_a_headers, control_code="GET-001")
        res = client.get(f"/api/v1/compliance/controls/{ctrl['id']}", headers=org_a_headers)
        assert res.status_code == 200
        assert res.json()["id"] == ctrl["id"]

    def test_get_nonexistent_control(self, client, org_a_headers):
        res = client.get(f"/api/v1/compliance/controls/{uuid.uuid4()}", headers=org_a_headers)
        assert res.status_code == 404

    def test_update_control(self, client, org_a_headers):
        ctrl = _create_control(client, org_a_headers, control_code="UPD-001")
        res = client.patch(
            f"/api/v1/compliance/controls/{ctrl['id']}",
            headers=org_a_headers,
            json={"name": "Updated Policy", "status": "inactive"},
        )
        assert res.status_code == 200
        assert res.json()["name"] == "Updated Policy"
        assert res.json()["status"] == "inactive"

    def test_delete_control(self, client, org_a_headers):
        ctrl = _create_control(client, org_a_headers, control_code="DEL-001")
        res = client.delete(f"/api/v1/compliance/controls/{ctrl['id']}", headers=org_a_headers)
        assert res.status_code == 200
        assert "deleted" in res.json()["message"].lower()
        # Verify gone
        res2 = client.get(f"/api/v1/compliance/controls/{ctrl['id']}", headers=org_a_headers)
        assert res2.status_code == 404


# ===========================================================================
# 2. COMPLIANCE TASK CRUD
# ===========================================================================

class TestComplianceTaskCRUD:

    def test_create_task(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, title="Quarterly Audit")
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Quarterly Audit"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"

    def test_create_task_with_control(self, client, org_a_headers):
        ctrl = _create_control(client, org_a_headers, control_code="TC-001")
        res = _create_task(client, org_a_headers, title="Linked Task", control_id=ctrl["id"])
        assert res.status_code == 201
        assert res.json()["control_id"] == ctrl["id"]

    def test_create_task_invalid_control(self, client, org_a_headers):
        """Referencing a nonexistent control should fail with 400."""
        res = _create_task(client, org_a_headers, control_id=str(uuid.uuid4()))
        assert res.status_code == 400
        assert "not found" in res.json()["detail"].lower()

    def test_list_tasks(self, client, org_a_headers):
        _create_task(client, org_a_headers, title="Task A1")
        _create_task(client, org_a_headers, title="Task A2")
        res = client.get("/api/v1/compliance/tasks", headers=org_a_headers)
        assert res.status_code == 200
        assert res.json()["total"] >= 2

    def test_list_tasks_pagination(self, client, org_a_headers):
        for i in range(5):
            _create_task(client, org_a_headers, title=f"Page Task {i}")
        res = client.get("/api/v1/compliance/tasks?skip=0&limit=2", headers=org_a_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) <= 2
        assert data["total"] >= 5

    def test_list_tasks_filter_by_priority(self, client, org_a_headers):
        _create_task(client, org_a_headers, title="High Prio", priority="high")
        _create_task(client, org_a_headers, title="Low Prio", priority="low")
        res = client.get("/api/v1/compliance/tasks?priority=high", headers=org_a_headers)
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["priority"] == "high"

    def test_get_task_by_id(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, title="Fetch Me")
        task_id = res.json()["id"]
        get_res = client.get(f"/api/v1/compliance/tasks/{task_id}", headers=org_a_headers)
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "Fetch Me"

    def test_get_nonexistent_task(self, client, org_a_headers):
        res = client.get(f"/api/v1/compliance/tasks/{uuid.uuid4()}", headers=org_a_headers)
        assert res.status_code == 404

    def test_update_task(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, title="Update Me")
        task_id = res.json()["id"]
        patch_res = client.patch(
            f"/api/v1/compliance/tasks/{task_id}",
            headers=org_a_headers,
            json={"title": "Updated Title", "priority": "high"},
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["title"] == "Updated Title"
        assert patch_res.json()["priority"] == "high"

    def test_delete_task(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, title="Delete Me")
        task_id = res.json()["id"]
        del_res = client.delete(f"/api/v1/compliance/tasks/{task_id}", headers=org_a_headers)
        assert del_res.status_code == 200
        assert "deleted" in del_res.json()["message"].lower()
        # Verify gone
        assert client.get(f"/api/v1/compliance/tasks/{task_id}", headers=org_a_headers).status_code == 404


# ===========================================================================
# 3. STATUS TRANSITIONS & OVERDUE LOGIC
# ===========================================================================

class TestStatusAndOverdue:

    def test_mark_task_completed(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, title="Complete Me")
        task_id = res.json()["id"]
        patch = client.patch(
            f"/api/v1/compliance/tasks/{task_id}",
            headers=org_a_headers,
            json={"status": "completed"},
        )
        assert patch.status_code == 200
        data = patch.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_overdue_auto_detection_on_create(self, client, org_a_headers):
        """A task with a past due date should be automatically marked overdue."""
        past = (date.today() - timedelta(days=5)).isoformat()
        res = _create_task(client, org_a_headers, title="Past Due Task", due_date=past)
        assert res.status_code == 201
        assert res.json()["status"] == "overdue"

    def test_completed_task_not_marked_overdue(self, client, org_a_headers):
        """A completed task with a past due date must NOT be re-marked overdue."""
        past = (date.today() - timedelta(days=3)).isoformat()
        res = _create_task(client, org_a_headers, title="Done Task", due_date=past, status="completed")
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "completed"

    def test_overdue_on_get(self, client, org_a_headers):
        """Getting a task with a past due date should dynamically mark it overdue."""
        future = (date.today() + timedelta(days=1)).isoformat()
        res = _create_task(client, org_a_headers, title="Soon Due", due_date=future)
        assert res.status_code == 201
        task_id = res.json()["id"]
        # Manually set due_date to the past via PATCH
        past = (date.today() - timedelta(days=1)).isoformat()
        client.patch(
            f"/api/v1/compliance/tasks/{task_id}",
            headers=org_a_headers,
            json={"due_date": past},
        )
        # GET should detect overdue dynamically
        get_res = client.get(f"/api/v1/compliance/tasks/{task_id}", headers=org_a_headers)
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "overdue"

    def test_filter_overdue(self, client, org_a_headers):
        """Filtering by status=overdue should include dynamically overdue tasks."""
        past = (date.today() - timedelta(days=10)).isoformat()
        _create_task(client, org_a_headers, title="Overdue Filter", due_date=past)
        res = client.get("/api/v1/compliance/tasks?status=overdue", headers=org_a_headers)
        assert res.status_code == 200
        titles = [t["title"] for t in res.json()["items"]]
        assert "Overdue Filter" in titles


# ===========================================================================
# 4. PRIORITY VALIDATION
# ===========================================================================

class TestPriorityValidation:

    def test_valid_priorities(self, client, org_a_headers):
        for prio in ("low", "medium", "high", "critical"):
            res = _create_task(client, org_a_headers, title=f"Prio {prio}", priority=prio)
            assert res.status_code == 201

    def test_invalid_priority_rejected(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, priority="extreme")
        assert res.status_code == 422


# ===========================================================================
# 5. DUE DATE VALIDATION
# ===========================================================================

class TestDueDateValidation:

    def test_task_with_future_due_date(self, client, org_a_headers):
        future = (date.today() + timedelta(days=30)).isoformat()
        res = _create_task(client, org_a_headers, title="Future Task", due_date=future)
        assert res.status_code == 201
        assert res.json()["due_date"] == future
        assert res.json()["status"] == "pending"

    def test_update_due_date(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, title="Change Date")
        task_id = res.json()["id"]
        new_date = (date.today() + timedelta(days=14)).isoformat()
        patch = client.patch(
            f"/api/v1/compliance/tasks/{task_id}",
            headers=org_a_headers,
            json={"due_date": new_date},
        )
        assert patch.status_code == 200
        assert patch.json()["due_date"] == new_date


# ===========================================================================
# 6. DASHBOARD STATISTICS
# ===========================================================================

class TestComplianceDashboard:

    def test_dashboard_metrics(self, client, org_a_headers):
        """Create a mix of tasks and controls and verify dashboard aggregation."""
        # Create controls
        _create_control(client, org_a_headers, name="Dash Ctrl 1", control_code="DASH-C1")
        _create_control(client, org_a_headers, name="Dash Ctrl 2", control_code="DASH-C2")

        # Create tasks
        _create_task(client, org_a_headers, title="Dash Pending", status="pending")
        _create_task(client, org_a_headers, title="Dash InProgress", status="in_progress")
        _create_task(client, org_a_headers, title="Dash Completed", status="completed")
        past = (date.today() - timedelta(days=2)).isoformat()
        _create_task(client, org_a_headers, title="Dash Overdue", due_date=past)

        # Due within 7 days
        soon = (date.today() + timedelta(days=3)).isoformat()
        _create_task(client, org_a_headers, title="Dash Soon", due_date=soon)

        res = client.get("/api/v1/compliance/dashboard", headers=org_a_headers)
        assert res.status_code == 200
        data = res.json()

        assert data["total_tasks"] >= 5
        assert data["pending_tasks"] >= 1
        assert data["in_progress_tasks"] >= 1
        assert data["completed_tasks"] >= 1
        assert data["overdue_tasks"] >= 1
        assert data["tasks_due_next_7_days"] >= 1
        assert data["compliance_controls_count"] >= 2
        assert 0.0 <= data["completion_percentage"] <= 100.0

    def test_dashboard_empty_org(self, client, org_b_headers):
        """Dashboard for an org with no tasks/controls should return zeros."""
        res = client.get("/api/v1/compliance/dashboard", headers=org_b_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_tasks"] == 0
        assert data["completion_percentage"] == 0.0
        assert data["compliance_controls_count"] == 0


# ===========================================================================
# 7. AUDIT LOG CREATION
# ===========================================================================

class TestAuditLogging:

    def test_control_crud_audit_logs(self, client, org_a_headers, db_session):
        from app.models import AuditLog
        from sqlalchemy import select

        ctrl = _create_control(client, org_a_headers, name="Audit Ctrl", control_code="AUD-C01")
        ctrl_id = uuid.UUID(ctrl["id"])

        # Update
        client.patch(
            f"/api/v1/compliance/controls/{ctrl['id']}",
            headers=org_a_headers,
            json={"name": "Audited Updated"},
        )
        # Delete
        client.delete(f"/api/v1/compliance/controls/{ctrl['id']}", headers=org_a_headers)

        logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "ComplianceControl",
                AuditLog.entity_id == ctrl_id,
            )
        ).scalars().all()

        events = [l.details.get("event") for l in logs if l.details]
        assert "control_created" in events
        assert "control_updated" in events
        assert "control_deleted" in events

    def test_task_crud_audit_logs(self, client, org_a_headers, db_session):
        from app.models import AuditLog
        from sqlalchemy import select

        res = _create_task(client, org_a_headers, title="Audit Task")
        task_id = uuid.UUID(res.json()["id"])

        # Update
        client.patch(
            f"/api/v1/compliance/tasks/{task_id}",
            headers=org_a_headers,
            json={"title": "Audited Task Update"},
        )
        # Complete
        client.patch(
            f"/api/v1/compliance/tasks/{task_id}",
            headers=org_a_headers,
            json={"status": "completed"},
        )
        # Delete
        client.delete(f"/api/v1/compliance/tasks/{task_id}", headers=org_a_headers)

        logs = db_session.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "ComplianceTask",
                AuditLog.entity_id == task_id,
            )
        ).scalars().all()

        events = [l.details.get("event") for l in logs if l.details]
        assert "task_created" in events
        assert "task_updated" in events
        assert "task_marked_completed" in events
        assert "task_deleted" in events


# ===========================================================================
# 8. INVALID RELATED RECORD IDS
# ===========================================================================

class TestInvalidRelatedRecords:

    def test_invalid_control_id(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, control_id=str(uuid.uuid4()))
        assert res.status_code == 400

    def test_invalid_contract_id(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, contract_id=str(uuid.uuid4()))
        assert res.status_code == 400

    def test_invalid_obligation_id(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, obligation_id=str(uuid.uuid4()))
        assert res.status_code == 400

    def test_invalid_assignee_id(self, client, org_a_headers):
        res = _create_task(client, org_a_headers, assignee_id=str(uuid.uuid4()))
        assert res.status_code == 400


# ===========================================================================
# 9. CROSS-ORGANIZATION ACCESS PREVENTION
# ===========================================================================

class TestCrossOrgIsolation:

    def test_control_cross_org_get(self, client, org_a_headers, org_b_headers):
        ctrl = _create_control(client, org_a_headers, control_code="CROSS-C1")
        res = client.get(f"/api/v1/compliance/controls/{ctrl['id']}", headers=org_b_headers)
        assert res.status_code == 404

    def test_control_cross_org_update(self, client, org_a_headers, org_b_headers):
        ctrl = _create_control(client, org_a_headers, control_code="CROSS-C2")
        res = client.patch(
            f"/api/v1/compliance/controls/{ctrl['id']}",
            headers=org_b_headers,
            json={"name": "Hacked"},
        )
        assert res.status_code == 404

    def test_control_cross_org_delete(self, client, org_a_headers, org_b_headers):
        ctrl = _create_control(client, org_a_headers, control_code="CROSS-C3")
        res = client.delete(f"/api/v1/compliance/controls/{ctrl['id']}", headers=org_b_headers)
        assert res.status_code == 404

    def test_task_cross_org_get(self, client, org_a_headers, org_b_headers):
        res = _create_task(client, org_a_headers, title="A's Task")
        task_id = res.json()["id"]
        res2 = client.get(f"/api/v1/compliance/tasks/{task_id}", headers=org_b_headers)
        assert res2.status_code == 404

    def test_task_cross_org_update(self, client, org_a_headers, org_b_headers):
        res = _create_task(client, org_a_headers, title="A's Task 2")
        task_id = res.json()["id"]
        res2 = client.patch(
            f"/api/v1/compliance/tasks/{task_id}",
            headers=org_b_headers,
            json={"title": "Hacked"},
        )
        assert res2.status_code == 404

    def test_task_cross_org_delete(self, client, org_a_headers, org_b_headers):
        res = _create_task(client, org_a_headers, title="A's Task 3")
        task_id = res.json()["id"]
        res2 = client.delete(f"/api/v1/compliance/tasks/{task_id}", headers=org_b_headers)
        assert res2.status_code == 404

    def test_task_cross_org_control_reference(self, client, org_a_headers, org_b_headers):
        """Org B cannot create a task referencing Org A's control."""
        ctrl = _create_control(client, org_a_headers, control_code="CROSS-C4")
        res = _create_task(client, org_b_headers, title="Sneaky Task", control_id=ctrl["id"])
        assert res.status_code == 400

    def test_dashboard_isolation(self, client, org_a_headers, org_b_headers):
        """Org B's dashboard must not include Org A's data."""
        _create_control(client, org_a_headers, control_code="ISO-D1")
        _create_task(client, org_a_headers, title="Org A Only Task")
        res = client.get("/api/v1/compliance/dashboard", headers=org_b_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_tasks"] == 0
        assert data["compliance_controls_count"] == 0


# ===========================================================================
# 10. UNAUTHORIZED ACCESS
# ===========================================================================

class TestUnauthorizedAccess:

    def test_controls_require_auth(self, client):
        assert client.get("/api/v1/compliance/controls").status_code == 401
        assert client.post("/api/v1/compliance/controls", json={"name": "x", "description": "x"}).status_code == 401

    def test_tasks_require_auth(self, client):
        assert client.get("/api/v1/compliance/tasks").status_code == 401
        assert client.post("/api/v1/compliance/tasks", json={"title": "x"}).status_code == 401

    def test_dashboard_requires_auth(self, client):
        assert client.get("/api/v1/compliance/dashboard").status_code == 401

    def test_control_detail_requires_auth(self, client):
        assert client.get(f"/api/v1/compliance/controls/{uuid.uuid4()}").status_code == 401
        assert client.patch(f"/api/v1/compliance/controls/{uuid.uuid4()}", json={"name": "x"}).status_code == 401
        assert client.delete(f"/api/v1/compliance/controls/{uuid.uuid4()}").status_code == 401

    def test_task_detail_requires_auth(self, client):
        assert client.get(f"/api/v1/compliance/tasks/{uuid.uuid4()}").status_code == 401
        assert client.patch(f"/api/v1/compliance/tasks/{uuid.uuid4()}", json={"title": "x"}).status_code == 401
        assert client.delete(f"/api/v1/compliance/tasks/{uuid.uuid4()}").status_code == 401
