import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_organization, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import AuditAction, AuditLog, Organization, User, UserRole
from app.schemas.auth import (
    LoginRequest,
    OrganizationResponse,
    RegisterResponse,
    TokenResponse,
    UserProfileResponse,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter()


def _generate_org_slug(name: str, db: Session) -> str:
    """
    Generate a URL-safe, unique organization slug from its display name.
    """
    base_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not base_slug:
        base_slug = "org"
    base_slug = base_slug[:80]

    slug = base_slug
    counter = 1
    while db.execute(select(Organization).filter_by(slug=slug)).scalar_one_or_none() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:
            slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            break
    return slug


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new organization and owner account",
    description="Atomically creates an organization and its first user (assigned the OWNER role) in one transaction.",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    # 1. Normalize and check for duplicate email
    normalized_email = payload.email.strip().lower()
    existing_user = db.execute(
        select(User).filter_by(email=normalized_email)
    ).scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # 2. Hash password securely using Argon2id
    hashed_pw = get_password_hash(payload.password)

    # 3. Create Organization and User atomically
    slug = _generate_org_slug(payload.organization_name, db)
    org = Organization(
        name=payload.organization_name.strip(),
        slug=slug,
        is_active=True,
    )
    db.add(org)
    db.flush()  # Flush to generate org.id

    user = User(
        organization_id=org.id,
        email=normalized_email,
        full_name=payload.full_name.strip(),
        hashed_password=hashed_pw,
        role=UserRole.OWNER.value,
        is_active=True,
    )
    db.add(user)
    db.flush()  # Flush to generate user.id

    # 4. Create Audit Log entry
    audit = AuditLog(
        organization_id=org.id,
        user_id=user.id,
        action=AuditAction.CREATE.value,
        entity_type="User",
        entity_id=user.id,
        details={
            "event": "user_registration",
            "organization_name": org.name,
            "organization_slug": org.slug,
            "role": user.role,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(org)
    db.refresh(user)

    # 5. Generate initial access token
    access_token = create_access_token(
        subject=user.id,
        organization_id=org.id,
    )

    return RegisterResponse(
        message="User and organization registered successfully.",
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org),
        access_token=access_token,
        token_type="bearer",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login and JWT token issuance",
    description="Validates user credentials and issues a signed JWT access token containing user and tenant claims.",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    normalized_email = payload.email.strip().lower()

    # Query user by normalized email
    user = db.execute(
        select(User).filter_by(email=normalized_email)
    ).scalar_one_or_none()

    # Use safe constant-time or safe error reporting for invalid user or password
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    # Issue signed JWT access token
    access_token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id,
    )

    # Record login audit log
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action=AuditAction.LOGIN.value,
        entity_type="User",
        entity_id=user.id,
        details={"event": "user_login"},
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the profile and tenant organization context of the authenticated user. Requires valid JWT.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    current_org: Organization = Depends(get_current_organization),
) -> UserProfileResponse:
    return UserProfileResponse(
        id=current_user.id,
        organization_id=current_user.organization_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        organization=OrganizationResponse.model_validate(current_org),
    )
