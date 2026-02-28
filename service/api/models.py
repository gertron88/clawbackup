"""
Pydantic models for ClawBackup API
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class AgentRegistration(BaseModel):
    """Request to register a new agent."""
    agent_name: str = Field(..., min_length=3, max_length=64, regex=r"^[a-zA-Z0-9_-]+$")
    moltbook_username: Optional[str] = Field(None, description="Moltbook username (e.g., @myagent)")
    contact_email: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent information (returned on registration)."""
    agent_id: str
    agent_name: str
    moltbook_username: Optional[str]
    tier: str = "free"
    storage_quota_gb: float
    storage_used_gb: float
    api_key: Optional[str] = Field(None, description="Only shown on registration!")
    created_at: datetime
    backup_count: int = 0


class BackupMetadata(BaseModel):
    """Metadata for a backup."""
    backup_id: str
    agent_id: str
    name: str
    size_bytes: int
    content_hash: str  # SHA-256 of encrypted content
    encryption_key_hash: Optional[str] = None  # Hash for verification (not the key itself)
    tags: List[str] = []
    created_at: datetime
    expires_at: datetime
    storage_key: str  # Internal S3 key


class BackupCreateResponse(BaseModel):
    """Response after creating a backup."""
    backup_id: str
    status: str
    size_bytes: int
    storage_url: str
    expires_at: datetime
    content_hash: str


class BackupListResponse(BaseModel):
    """Paginated list of backups."""
    backups: List[BackupMetadata]
    total: int
    limit: int
    offset: int


class RestoreRequest(BaseModel):
    """Request to restore a backup."""
    target_agent_id: Optional[str] = None
    encryption_key_hash: Optional[str] = None  # For verification


class WebhookRegistration(BaseModel):
    """Register a webhook."""
    url: HttpUrl
    events: List[str] = Field(default=["*"], description="Events to subscribe to: backup.created, backup.deleted, etc.")
    secret: Optional[str] = None  # For HMAC signature verification


class APIKey(BaseModel):
    """API key information."""
    key_id: str
    agent_id: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
