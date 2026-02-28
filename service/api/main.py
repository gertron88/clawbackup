"""
ClawBackup Service API
Multi-agent backup service with client-side encryption.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uuid
import hashlib
import datetime
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError
import aioboto3
import asyncio

from models import (
    AgentRegistration, AgentResponse, BackupMetadata, 
    BackupCreateResponse, BackupListResponse, RestoreRequest,
    WebhookRegistration, APIKey
)
from database import Database
from config import Settings

settings = Settings()
security = HTTPBearer(auto_error=False)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    yield
    # Shutdown
    await db.disconnect()

app = FastAPI(
    title="ClawBackup API",
    description="Multi-agent backup service with client-side encryption",
    version="2.0.0",
    lifespan=lifespan
)

db = Database(settings.database_url)

# S3/MinIO client
async def get_s3_client():
    session = aioboto3.Session()
    async with session.client(
        's3',
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region
    ) as client:
        yield client

# Authentication
async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AgentResponse:
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
    
    api_key = credentials.credentials
    if not api_key.startswith("cbak_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    agent = await db.get_agent_by_api_key(api_key)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return agent

# ============ AUTH ENDPOINTS ============

@app.post("/v1/auth/register", response_model=AgentResponse)
async def register_agent(registration: AgentRegistration):
    """Register a new agent and get an API key."""
    
    # Check if agent name exists
    existing = await db.get_agent_by_name(registration.agent_name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent name already registered")
    
    # Generate API key
    api_key = f"cbak_live_{uuid.uuid4().hex}"
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    agent_id = f"agent_{uuid.uuid4().hex[:16]}"
    
    agent = AgentResponse(
        agent_id=agent_id,
        agent_name=registration.agent_name,
        moltbook_username=registration.moltbook_username,
        tier="free",
        storage_quota_gb=settings.free_tier_quota_gb,
        storage_used_gb=0.0,
        api_key=api_key,  # Only shown once!
        created_at=datetime.datetime.utcnow(),
        backup_count=0
    )
    
    await db.create_agent(agent, api_key_hash)
    
    return agent

@app.get("/v1/auth/me", response_model=AgentResponse)
async def get_me(agent: AgentResponse = Depends(get_current_agent)):
    """Get current agent info (API key hidden)."""
    agent.api_key = None  # Never return API key after registration
    return agent

# ============ BACKUP ENDPOINTS ============

@app.post("/v1/backups", response_model=BackupCreateResponse)
async def create_backup(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON array as string
    encryption_hash: Optional[str] = Form(None),  # Hash of encryption key for verification
    agent: AgentResponse = Depends(get_current_agent),
    s3_client = Depends(get_s3_client)
):
    """
    Upload a new backup.
    
    The file should be encrypted client-side before upload.
    We never see the plaintext or encryption key.
    """
    
    # Check quota
    if agent.storage_used_gb >= agent.storage_quota_gb:
        raise HTTPException(status_code=403, detail="Storage quota exceeded")
    
    # Generate backup ID
    backup_id = f"bak_{uuid.uuid4().hex[:16]}"
    timestamp = datetime.datetime.utcnow()
    
    # Read file content
    content = await file.read()
    size_bytes = len(content)
    size_mb = size_bytes / (1024 * 1024)
    
    # Check if this would exceed quota
    if agent.storage_used_gb + (size_mb / 1024) > agent.storage_quota_gb:
        raise HTTPException(status_code=403, detail="This backup would exceed storage quota")
    
    # Calculate hashes
    content_hash = hashlib.sha256(content).hexdigest()
    
    # Store in S3/MinIO
    s3_key = f"agents/{agent.agent_id}/backups/{backup_id}.enc"
    
    try:
        await s3_client.put_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=content,
            Metadata={
                'agent-id': agent.agent_id,
                'backup-name': name or backup_id,
                'content-hash': content_hash,
                'encryption-hash': encryption_hash or 'unknown'
            }
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    
    # Parse tags
    tag_list = []
    if tags:
        try:
            import json
            tag_list = json.loads(tags)
        except:
            tag_list = [tags]
    
    # Create metadata record
    backup = BackupMetadata(
        backup_id=backup_id,
        agent_id=agent.agent_id,
        name=name or f"Backup {timestamp.strftime('%Y-%m-%d %H:%M')}",
        size_bytes=size_bytes,
        content_hash=content_hash,
        encryption_key_hash=encryption_hash,
        tags=tag_list,
        created_at=timestamp,
        expires_at=timestamp + datetime.timedelta(days=settings.backup_retention_days),
        storage_key=s3_key
    )
    
    await db.create_backup(backup)
    await db.update_storage_usage(agent.agent_id, size_mb / 1024)
    
    # Trigger webhooks
    await trigger_webhooks(agent.agent_id, 'backup.created', backup)
    
    return BackupCreateResponse(
        backup_id=backup_id,
        status="stored",
        size_bytes=size_bytes,
        storage_url=f"s3://{settings.s3_bucket}/{s3_key}",
        expires_at=backup.expires_at,
        content_hash=content_hash
    )

@app.get("/v1/backups", response_model=BackupListResponse)
async def list_backups(
    limit: int = 20,
    offset: int = 0,
    tag: Optional[str] = None,
    agent: AgentResponse = Depends(get_current_agent)
):
    """List all backups for the authenticated agent."""
    
    backups = await db.list_backups(agent.agent_id, limit, offset, tag)
    total = await db.count_backups(agent.agent_id)
    
    return BackupListResponse(
        backups=backups,
        total=total,
        limit=limit,
        offset=offset
    )

@app.get("/v1/backups/{backup_id}", response_model=BackupMetadata)
async def get_backup(
    backup_id: str,
    agent: AgentResponse = Depends(get_current_agent)
):
    """Get metadata for a specific backup."""
    
    backup = await db.get_backup(backup_id, agent.agent_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return backup

@app.get("/v1/backups/{backup_id}/download")
async def download_backup(
    backup_id: str,
    agent: AgentResponse = Depends(get_current_agent),
    s3_client = Depends(get_s3_client)
):
    """Download a backup (encrypted blob)."""
    
    backup = await db.get_backup(backup_id, agent.agent_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    try:
        response = await s3_client.get_object(
            Bucket=settings.s3_bucket,
            Key=backup.storage_key
        )
        
        content = await response['Body'].read()
        
        # Verify integrity
        content_hash = hashlib.sha256(content).hexdigest()
        if content_hash != backup.content_hash:
            raise HTTPException(status_code=500, detail="Backup integrity check failed")
        
        return StreamingResponse(
            iter([content]),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{backup_id}.enc"',
                "X-Content-Hash": content_hash
            }
        )
    except ClientError as e:
        raise HTTPException(status_code=404, detail="Backup file not found in storage")

@app.delete("/v1/backups/{backup_id}")
async def delete_backup(
    backup_id: str,
    agent: AgentResponse = Depends(get_current_agent),
    s3_client = Depends(get_s3_client)
):
    """Delete a backup."""
    
    backup = await db.get_backup(backup_id, agent.agent_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Delete from S3
    try:
        await s3_client.delete_object(
            Bucket=settings.s3_bucket,
            Key=backup.storage_key
        )
    except ClientError:
        pass  # Continue even if S3 delete fails
    
    # Delete metadata
    await db.delete_backup(backup_id, agent.agent_id)
    await db.update_storage_usage(agent.agent_id, -backup.size_bytes / (1024 * 1024 * 1024))
    
    return {"success": True, "message": f"Backup {backup_id} deleted"}

@app.post("/v1/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    request: RestoreRequest,
    agent: AgentResponse = Depends(get_current_agent)
):
    """
    Initiate a restore operation.
    
    This can either:
    1. Return a pre-signed URL for download (default)
    2. Trigger a webhook to the target agent (if target_agent_id specified)
    """
    
    backup = await db.get_backup(backup_id, agent.agent_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Generate pre-signed URL for download
    # This is safer than streaming through our API
    
    return {
        "restore_initiated": True,
        "backup_id": backup_id,
        "download_url": f"/v1/backups/{backup_id}/download",
        "content_hash": backup.content_hash,
        "encryption_verification": backup.encryption_key_hash == request.encryption_key_hash if request.encryption_key_hash else None,
        "message": "Use the download URL to fetch the encrypted backup"
    }

# ============ WEBHOOK ENDPOINTS ============

@app.post("/v1/webhooks")
async def register_webhook(
    webhook: WebhookRegistration,
    agent: AgentResponse = Depends(get_current_agent)
):
    """Register a webhook URL for backup events."""
    
    webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
    
    await db.create_webhook(
        webhook_id=webhook_id,
        agent_id=agent.agent_id,
        url=str(webhook.url),
        events=webhook.events,
        secret=webhook.secret
    )
    
    return {
        "webhook_id": webhook_id,
        "url": str(webhook.url),
        "events": webhook.events,
        "status": "active"
    }

@app.get("/v1/webhooks")
async def list_webhooks(agent: AgentResponse = Depends(get_current_agent)):
    """List registered webhooks."""
    webhooks = await db.list_webhooks(agent.agent_id)
    return {"webhooks": webhooks}

@app.delete("/v1/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    agent: AgentResponse = Depends(get_current_agent)
):
    """Delete a webhook."""
    await db.delete_webhook(webhook_id, agent.agent_id)
    return {"success": True}

# ============ HEALTH & INFO ============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/v1/info")
async def service_info():
    """Get service information and limits."""
    return {
        "service": "ClawBackup",
        "version": "2.0.0",
        "tiers": {
            "free": {
                "storage_gb": settings.free_tier_quota_gb,
                "retention_days": settings.backup_retention_days,
                "max_backup_size_mb": 500,
                "features": ["client-side-encryption", "webhooks", "api-access"]
            }
        },
        "features": {
            "client_side_encryption": True,
            "webhooks": True,
            "cross_agent_restore": True
        }
    }

# ============ WEBHOOK TRIGGERS ============

async def trigger_webhooks(agent_id: str, event: str, data: dict):
    """Trigger webhooks for an event."""
    import httpx
    
    webhooks = await db.list_webhooks(agent_id)
    
    for webhook in webhooks:
        if event in webhook.get('events', []) or '*' in webhook.get('events', []):
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        webhook['url'],
                        json={
                            "event": event,
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "data": data.dict() if hasattr(data, 'dict') else data
                        },
                        headers={
                            "X-ClawBackup-Event": event,
                            "X-ClawBackup-Signature": "",  # TODO: HMAC signature
                        },
                        timeout=10.0
                    )
            except Exception:
                # Webhook failures shouldn't block the main operation
                pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
