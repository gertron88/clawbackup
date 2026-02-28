"""
Database layer for ClawBackup API
Uses async PostgreSQL
"""

import asyncpg
from typing import Optional, List
from models import AgentResponse, BackupMetadata
import json


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize database connection pool."""
        self.pool = await asyncpg.create_pool(self.database_url)
        await self._create_tables()
    
    async def disconnect(self):
        """Close database connections."""
        if self.pool:
            await self.pool.close()
    
    async def _create_tables(self):
        """Create tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Agents table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    agent_name TEXT UNIQUE NOT NULL,
                    moltbook_username TEXT,
                    contact_email TEXT,
                    tier TEXT DEFAULT 'free',
                    storage_quota_gb REAL DEFAULT 1.0,
                    storage_used_gb REAL DEFAULT 0.0,
                    api_key_hash TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    backup_count INTEGER DEFAULT 0
                )
            """)
            
            # Backups table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    agent_id TEXT REFERENCES agents(agent_id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    encryption_key_hash TEXT,
                    tags JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP NOT NULL,
                    storage_key TEXT NOT NULL
                )
            """)
            
            # Webhooks table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    webhook_id TEXT PRIMARY KEY,
                    agent_id TEXT REFERENCES agents(agent_id) ON DELETE CASCADE,
                    url TEXT NOT NULL,
                    events JSONB DEFAULT '["*"]',
                    secret TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_triggered_at TIMESTAMP
                )
            """)
    
    # Agent operations
    async def create_agent(self, agent: AgentResponse, api_key_hash: str):
        """Create a new agent."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agents (agent_id, agent_name, moltbook_username, 
                    contact_email, tier, storage_quota_gb, storage_used_gb, 
                    api_key_hash, created_at, backup_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                agent.agent_id,
                agent.agent_name,
                agent.moltbook_username,
                None,  # contact_email not in AgentResponse yet
                agent.tier,
                agent.storage_quota_gb,
                agent.storage_used_gb,
                api_key_hash,
                agent.created_at,
                agent.backup_count
            )
    
    async def get_agent_by_api_key(self, api_key: str) -> Optional[AgentResponse]:
        """Get agent by API key."""
        api_key_hash = hash(api_key)  # Simple hash for demo - use proper hash in prod
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agents WHERE api_key_hash = $1",
                api_key_hash
            )
            if row:
                return AgentResponse(
                    agent_id=row['agent_id'],
                    agent_name=row['agent_name'],
                    moltbook_username=row['moltbook_username'],
                    tier=row['tier'],
                    storage_quota_gb=row['storage_quota_gb'],
                    storage_used_gb=row['storage_used_gb'],
                    api_key=None,
                    created_at=row['created_at'],
                    backup_count=row['backup_count']
                )
            return None
    
    async def get_agent_by_name(self, agent_name: str) -> Optional[AgentResponse]:
        """Check if agent name exists."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT agent_id FROM agents WHERE agent_name = $1",
                agent_name
            )
            if row:
                return AgentResponse(agent_id=row['agent_id'], agent_name=agent_name)
            return None
    
    async def update_storage_usage(self, agent_id: str, delta_gb: float):
        """Update storage usage."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE agents SET storage_used_gb = storage_used_gb + $1 WHERE agent_id = $2",
                delta_gb, agent_id
            )
    
    # Backup operations
    async def create_backup(self, backup: BackupMetadata):
        """Create backup metadata record."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO backups (backup_id, agent_id, name, size_bytes, 
                    content_hash, encryption_key_hash, tags, created_at, expires_at, storage_key)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                backup.backup_id,
                backup.agent_id,
                backup.name,
                backup.size_bytes,
                backup.content_hash,
                backup.encryption_key_hash,
                json.dumps(backup.tags),
                backup.created_at,
                backup.expires_at,
                backup.storage_key
            )
            # Increment backup count
            await conn.execute(
                "UPDATE agents SET backup_count = backup_count + 1 WHERE agent_id = $1",
                backup.agent_id
            )
    
    async def get_backup(self, backup_id: str, agent_id: str) -> Optional[BackupMetadata]:
        """Get backup by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM backups 
                WHERE backup_id = $1 AND agent_id = $2
                """,
                backup_id, agent_id
            )
            if row:
                return BackupMetadata(
                    backup_id=row['backup_id'],
                    agent_id=row['agent_id'],
                    name=row['name'],
                    size_bytes=row['size_bytes'],
                    content_hash=row['content_hash'],
                    encryption_key_hash=row['encryption_key_hash'],
                    tags=json.loads(row['tags']),
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    storage_key=row['storage_key']
                )
            return None
    
    async def list_backups(self, agent_id: str, limit: int, offset: int, tag: Optional[str] = None) -> List[BackupMetadata]:
        """List backups for agent."""
        async with self.pool.acquire() as conn:
            if tag:
                rows = await conn.fetch(
                    """
                    SELECT * FROM backups 
                    WHERE agent_id = $1 AND tags @> $4::jsonb
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    agent_id, limit, offset, json.dumps([tag])
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM backups 
                    WHERE agent_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    agent_id, limit, offset
                )
            
            return [
                BackupMetadata(
                    backup_id=row['backup_id'],
                    agent_id=row['agent_id'],
                    name=row['name'],
                    size_bytes=row['size_bytes'],
                    content_hash=row['content_hash'],
                    encryption_key_hash=row['encryption_key_hash'],
                    tags=json.loads(row['tags']),
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    storage_key=row['storage_key']
                )
                for row in rows
            ]
    
    async def count_backups(self, agent_id: str) -> int:
        """Count total backups for agent."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) FROM backups WHERE agent_id = $1",
                agent_id
            )
            return row[0]
    
    async def delete_backup(self, backup_id: str, agent_id: str):
        """Delete backup metadata."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM backups WHERE backup_id = $1 AND agent_id = $2",
                backup_id, agent_id
            )
            # Decrement backup count
            if result == "DELETE 1":
                await conn.execute(
                    "UPDATE agents SET backup_count = backup_count - 1 WHERE agent_id = $1",
                    agent_id
                )
    
    # Webhook operations
    async def create_webhook(self, webhook_id: str, agent_id: str, url: str, events: List[str], secret: Optional[str]):
        """Create webhook."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO webhooks (webhook_id, agent_id, url, events, secret)
                VALUES ($1, $2, $3, $4, $5)
                """,
                webhook_id, agent_id, url, json.dumps(events), secret
            )
    
    async def list_webhooks(self, agent_id: str) -> List[dict]:
        """List webhooks for agent."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM webhooks WHERE agent_id = $1",
                agent_id
            )
            return [
                {
                    "webhook_id": row['webhook_id'],
                    "url": row['url'],
                    "events": json.loads(row['events']),
                    "created_at": row['created_at']
                }
                for row in rows
            ]
    
    async def delete_webhook(self, webhook_id: str, agent_id: str):
        """Delete webhook."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM webhooks WHERE webhook_id = $1 AND agent_id = $2",
                webhook_id, agent_id
            )


def hash(api_key: str) -> str:
    """Hash API key for storage."""
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()
