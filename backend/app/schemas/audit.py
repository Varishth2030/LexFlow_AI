import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, computed_field


class AuditLogItemResponse(BaseModel):
    """
    Response schema for an audit log entry.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """
    Paginated list of audit logs for the authenticated tenant.
    """

    items: List[AuditLogItemResponse]
    total: int
    skip: int
    limit: int

    @computed_field
    @property
    def logs(self) -> List[AuditLogItemResponse]:
        """Convenience property for frontend consumers expecting a 'logs' array."""
        return self.items
