import uuid
from datetime import timedelta
import pytest
from sqlalchemy import select

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from app.models import AuditLog, Organization, User, UserRole


def test_password_hashing_utilities():
    """
    Test Argon2 password hashing and verification utilities.
    """
    raw_password = "SecurePassword123"
    hashed = get_password_hash(raw_password)

    # Verify hash structure (Argon2id)
    assert hashed.startswith("$argon2id$")
    assert raw_password not in hashed

    # Verify correct and incorrect password verification
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_password_strength_validation():
    """
    Test password complexity requirements.
    """
    # Valid password
    assert validate_password_strength("ValidPass1") == "ValidPass1"

    # Too short (< 8 chars)
    with pytest.raises(ValueError, match="at least 8 characters"):
        validate_password_strength("Short1")

    # No digit
    with pytest.raises(ValueError, match="at least one number"):
        validate_password_strength("NoDigitsHere")

    # No letter
    with pytest.raises(ValueError, match="at least one letter"):
        validate_password_strength("1234567890")


def test_successful_registration(client, db_session):
    """
    Test POST /api/v1/auth/register creates user and organization atomically.
    """
    payload = {
        "full_name": "Jane Doe",
        "email": "jane@lexflow.ai",
        "password": "Password123",
        "organization_name": "LexFlow Technologies",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "user" in data
    assert "organization" in data
    assert "access_token" in data

    # Verify safe user response (no password hash)
    user_data = data["user"]
    assert user_data["email"] == "jane@lexflow.ai"
    assert user_data["full_name"] == "Jane Doe"
    assert user_data["role"] == UserRole.OWNER.value
    assert "password" not in user_data
    assert "hashed_password" not in user_data

    # Verify organization response
    org_data = data["organization"]
    assert org_data["name"] == "LexFlow Technologies"
    assert org_data["slug"] == "lexflow-technologies"

    # Verify database persistence
    db_user = db_session.execute(select(User).filter_by(email="jane@lexflow.ai")).scalar_one_or_none()
    assert db_user is not None
    assert db_user.organization_id == uuid.UUID(org_data["id"])

    # Verify audit log was recorded
    audit = db_session.execute(
        select(AuditLog).filter_by(user_id=db_user.id)
    ).scalar_one_or_none()
    assert audit is not None
    assert audit.details.get("event") == "user_registration"


def test_registration_normalizes_email(client, db_session):
    """
    Test that email is stripped and lowercased during registration.
    """
    payload = {
        "full_name": "Uppercase User",
        "email": "  UPPERCASE@Example.COM  ",
        "password": "Password123",
        "organization_name": "Case Sensitivity Org",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "uppercase@example.com"

    db_user = db_session.execute(select(User).filter_by(email="uppercase@example.com")).scalar_one_or_none()
    assert db_user is not None


def test_duplicate_email_rejection(client):
    """
    Test that registering with an existing email returns HTTP 400.
    """
    payload = {
        "full_name": "First User",
        "email": "duplicate@lexflow.ai",
        "password": "Password123",
        "organization_name": "First Org",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "full_name": "Second User",
        "email": "duplicate@lexflow.ai",
        "password": "DifferentPassword123",
        "organization_name": "Second Org",
    }
    res2 = client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_successful_login(client):
    """
    Test POST /api/v1/auth/login validates credentials and returns JWT token.
    """
    # Register user
    reg_payload = {
        "full_name": "Login User",
        "email": "login@lexflow.ai",
        "password": "ValidLoginPassword123",
        "organization_name": "Login Corp",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login@lexflow.ai",
        "password": "ValidLoginPassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@lexflow.ai"


def test_incorrect_password_rejection(client):
    """
    Test login with wrong password returns HTTP 401.
    """
    reg_payload = {
        "full_name": "Wrong Pass User",
        "email": "wrongpass@lexflow.ai",
        "password": "CorrectPassword123",
        "organization_name": "Pass Corp",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpass@lexflow.ai",
        "password": "IncorrectPassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


def test_nonexistent_user_login(client):
    """
    Test login with non-existent email returns HTTP 401 without leaking existence.
    """
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@lexflow.ai",
        "password": "SomePassword123",
    })
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


def test_jwt_claims_validation():
    """
    Verify JWT payload claims structure (sub, org_id, exp, iat).
    """
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()

    token = create_access_token(subject=user_id, organization_id=org_id)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["org_id"] == str(org_id)
    assert "exp" in payload
    assert "iat" in payload


def test_expired_token_rejection(client, db_session):
    """
    Test that an expired JWT token returns HTTP 401.
    """
    org = Organization(name="Expired Org", slug="expired-org")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email="expired@lexflow.ai",
        full_name="Expired User",
        hashed_password="hash",
    )
    db_session.add(user)
    db_session.flush()

    # Generate token that expired 1 hour ago
    expired_token = create_access_token(
        subject=user.id,
        organization_id=org.id,
        expires_delta=timedelta(minutes=-60),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_protected_endpoint_me(client):
    """
    Test GET /api/v1/auth/me returns authenticated user and organization.
    """
    reg_payload = {
        "full_name": "Profile User",
        "email": "profile@lexflow.ai",
        "password": "ProfilePassword123",
        "organization_name": "Profile Org",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    profile = response.json()
    assert profile["email"] == "profile@lexflow.ai"
    assert profile["full_name"] == "Profile User"
    assert profile["organization"]["name"] == "Profile Org"
    assert "password" not in profile


def test_unauthenticated_request_rejection(client):
    """
    Test that accessing protected endpoint without token returns HTTP 401.
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_invalid_token_rejection(client):
    """
    Test that accessing protected endpoint with garbage token returns HTTP 401.
    """
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"},
    )
    assert response.status_code == 401


def test_inactive_user_rejection(client, db_session):
    """
    Test that deactivated users are blocked from logging in or using endpoints.
    """
    reg_payload = {
        "full_name": "Inactive User",
        "email": "inactive@lexflow.ai",
        "password": "Password123",
        "organization_name": "Deactivated Org",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    # Deactivate user in database
    db_user = db_session.execute(select(User).filter_by(email="inactive@lexflow.ai")).scalar_one()
    db_user.is_active = False
    db_session.commit()

    # Try accessing /me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 403
    assert "inactive" in me_res.json()["detail"].lower()

    # Try logging in
    login_res = client.post("/api/v1/auth/login", json={
        "email": "inactive@lexflow.ai",
        "password": "Password123",
    })
    assert login_res.status_code == 403
    assert "inactive" in login_res.json()["detail"].lower()


def test_organization_isolation_and_tenant_spoof_protection(client, db_session):
    """
    Verify organization isolation:
    1. Two different organizations have distinct users and data.
    2. A forged token with a mismatched organization claim is rejected.
    """
    # Org A
    client.post("/api/v1/auth/register", json={
        "full_name": "Org A Owner",
        "email": "owner@orga.com",
        "password": "Password123",
        "organization_name": "Tenant A Corp",
    })
    # Org B
    client.post("/api/v1/auth/register", json={
        "full_name": "Org B Owner",
        "email": "owner@orgb.com",
        "password": "Password123",
        "organization_name": "Tenant B Corp",
    })

    user_a = db_session.execute(select(User).filter_by(email="owner@orga.com")).scalar_one()
    user_b = db_session.execute(select(User).filter_by(email="owner@orgb.com")).scalar_one()

    assert user_a.organization_id != user_b.organization_id

    # Forged token: User A subject, but Org B tenant claim
    spoofed_token = create_access_token(
        subject=user_a.id,
        organization_id=user_b.organization_id,  # Spoofed!
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {spoofed_token}"},
    )
    assert response.status_code == 401
    assert "tenant context mismatch" in response.json()["detail"].lower()
