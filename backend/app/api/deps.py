import uuid
from typing import Generator, List, Optional
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User

# HTTP Bearer security scheme for OpenAPI documentation and token extraction
security = HTTPBearer(
    auto_error=False,
    description="JWT Bearer token. Enter the token obtained from /api/v1/auth/login",
)


def get_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> str:
    """
    Extract JWT bearer token from the Authorization header.
    Raises HTTP 401 if token is missing or malformed.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_token),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate JWT token, verify subject and tenant claim, and load current user from database.
    Rejects nonexistent or inactive users.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    token_org_id = payload.get("org_id")

    if not user_id_str or not token_org_id:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.execute(select(User).filter_by(id=user_uuid)).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    # Validate that token's organization claim matches the user's current organization
    if str(user.organization_id) != str(token_org_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tenant context mismatch.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Reusable dependency ensuring user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )
    return current_user


def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Organization:
    """
    Reusable dependency deriving tenant organization strictly from the authenticated user.
    Never trusts client-supplied organization_id.
    """
    org = db.execute(
        select(Organization).filter_by(id=current_user.organization_id)
    ).scalar_one_or_none()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    if not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization account is inactive.",
        )

    return org


def get_current_tenant_id(
    current_user: User = Depends(get_current_active_user),
) -> uuid.UUID:
    """
    Reusable dependency providing the organization UUID strictly from the authenticated user.
    Use this to scope all future database queries to the active tenant.
    """
    return current_user.organization_id


class RequireRole:
    """
    Role-based access control dependency factory.
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user


__all__ = [
    "get_db",
    "get_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_organization",
    "get_current_tenant_id",
    "RequireRole",
    "Session",
    "Generator",
]
