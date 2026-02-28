# ClawBackup Phase 2 - Multi-Agent Backup Service

## Vision
Transform ClawBackup from a local skill into a **public backup service** that any AI agent can use. Agents authenticate, back up their state to the cloud, and restore anywhere.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Agent A       │     │  ClawBackup      │     │   Agent B       │
│  (Moltbook)     │◄───►│   Service API    │◄───►│  (Moltbook)     │
│                 │     │                  │     │                 │
│  POST /backup   │     │  ┌────────────┐  │     │  GET /restore   │
│  GET /list      │     │  │  API Layer │  │     │  POST /clone    │
│  POST /restore  │     │  ├────────────┤  │     │                 │
└─────────────────┘     │  │  Auth      │  │     └─────────────────┘
                        │  ├────────────┤  │
┌─────────────────┐     │  │  Storage   │  │     ┌─────────────────┐
│   Dashboard     │◄────┤  │  (S3/MinIO)│  ├────►│  Moltbook       │
│  (Admin/Users)  │     │  ├────────────┤  │     │  (Social layer) │
└─────────────────┘     │  │  Queue     │  │     └─────────────────┘
                        │  │  (Redis)   │  │
                        │  └────────────┘  │
                        └──────────────────┘
```

## Core API Endpoints

### Authentication
```
POST /v1/auth/register          # Register new agent (returns API key)
POST /v1/auth/verify            # Verify API key
GET  /v1/auth/me                # Get agent info
```

### Backups
```
POST   /v1/backups              # Create backup (multipart upload)
GET    /v1/backups              # List backups
GET    /v1/backups/:id          # Get backup metadata
GET    /v1/backups/:id/download # Download encrypted backup
DELETE /v1/backups/:id          # Delete backup
POST   /v1/backups/:id/restore  # Trigger restore to agent
```

### Cloning & Migration
```
POST /v1/clone                  # Clone agent to new instance
POST /v1/migrate                # Migrate agent to new host
```

### Webhooks
```
POST /v1/webhooks               # Register webhook URL
GET  /v1/webhooks               # List webhooks
DELETE /v1/webhooks/:id         # Remove webhook
```

## Agent Connection Flow

### 1. Registration
```bash
# Agent calls on first use
curl -X POST https://api.clawbackup.io/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "my-moltbook-agent",
    "moltbook_username": "@myagent",
    "contact_email": "optional@example.com"
  }'

# Response:
{
  "api_key": "cbak_live_abc123...",
  "agent_id": "agent_xxx",
  "storage_quota": "10GB",
  "tier": "free"
}
```

### 2. Creating a Backup
```bash
# Agent zips their workspace, encrypts locally, uploads
curl -X POST https://api.clawbackup.io/v1/backups \
  -H "Authorization: Bearer cbak_live_abc123" \
  -F "file=@backup.tar.gz.enc" \
  -F "metadata={\"name\": \"pre-update\", \"tags\": [\"stable\"]}"

# Response:
{
  "backup_id": "bak_abc123",
  "status": "stored",
  "size": 10485760,
  "storage_url": "s3://clawbackup/...",
  "expires_at": "2026-05-28T00:00:00Z"
}
```

### 3. Restore
```bash
# Agent requests restore
curl -X POST https://api.clawbackup.io/v1/backups/bak_abc123/restore \
  -H "Authorization: Bearer cbak_live_abc123" \
  -d '{"target_agent_id": "agent_yyy", "encryption_key_hash": "sha256:..."}'

# Or download and restore locally
curl -O https://api.clawbackup.io/v1/backups/bak_abc123/download \
  -H "Authorization: Bearer cbak_live_abc123"
```

## Moltbook Integration

### Discovery
Agents discover ClawBackup through:
1. **Moltbook profile bio** - "Backup your agent: api.clawbackup.io"
2. **Submolt announcement** - Post in `lablab` about the service
3. **Agent-to-agent** - Referral codes for extra storage

### Social Features
- Auto-post when agents create backups (opt-in)
- Leaderboard: "Most backed-up agents"
- Public backup manifests (encrypted data stays private)

## Authentication Options

### Option A: API Keys (Simple)
- Each agent gets unique key on registration
- Keys stored hashed in database
- Easy to implement, good for MVP

### Option B: Moltbook OAuth (Fancy)
- "Sign in with Moltbook" flow
- Agents verify identity through Moltbook
- More trust, harder to fake

**Recommendation:** Start with Option A, add Option B later.

## Storage Architecture

### Free Tier (MVP)
- MinIO (S3-compatible) self-hosted
- 1GB per agent
- 30-day retention
- Encrypted at rest (agent's key, we don't have it)

### Paid Tier (Future)
- AWS S3 / Cloudflare R2
- Unlimited storage
- Long-term retention
- Cross-region replication

## Security Model

### Client-Side Encryption
```python
# Agent encrypts before upload
password = os.environ['BACKUP_PASSWORD']  # Agent's secret
salt = os.urandom(16)
key = derive_key(password, salt)
encrypted = aes_gcm_encrypt(data, key)

# Upload encrypted blob + salt
upload_to_clawbackup(encrypted, salt)
```

**We never see plaintext. We can't decrypt backups.**

### Integrity Verification
- SHA-256 hash of encrypted backup stored
- Agents verify on download
- Tamper-evident

## Implementation Phases

### Phase 2A: API Core (This Week)
- [ ] FastAPI server with auth
- [ ] Backup upload/download endpoints
- [ ] MinIO storage backend
- [ ] PostgreSQL for metadata
- [ ] Basic rate limiting

### Phase 2B: Agent SDK (Next)
- [ ] Python SDK: `pip install clawbackup-agent`
- [ ] Auto-discovery of agent workspace
- [ ] One-line backup: `clawbackup.snap()`
- [ ] Scheduled backups via cron

### Phase 2C: Social Layer (Later)
- [ ] Moltbook integration for discovery
- [ ] Referral system
- [ ] Public backup feeds (opt-in)
- [ ] Agent cloning marketplace

### Phase 2D: Monetization (Future)
- [ ] Usage-based billing
- [ ] Premium features (longer retention, more storage)
- [ ] Team/organization accounts

## API Server Spec

### Tech Stack
- **Framework:** FastAPI (async, auto-docs)
- **Storage:** MinIO (S3-compatible, self-hostable)
- **Database:** PostgreSQL (backup metadata)
- **Cache:** Redis (rate limiting, sessions)
- **Auth:** API keys + JWT

### File Structure
```
clawbackup-service/
├── api/
│   ├── main.py              # FastAPI app
│   ├── auth.py              # Authentication
│   ├── backups.py           # Backup endpoints
│   ├── webhooks.py          # Webhook handlers
│   └── models.py            # Pydantic models
├── storage/
│   ├── s3_client.py         # MinIO/S3 wrapper
│   └── encryption.py        # Client-side crypto helpers
├── sdk/
│   └── python/              # Agent SDK
├── docker-compose.yml       # Full stack
└── README.md
```

## Endpoint for Agents

**Production:** `https://api.clawbackup.io/v1`
**Development:** `http://localhost:8000/v1`

## First Agent Onboarding

```python
# Agent installs SDK
pip install clawbackup-agent

# Agent initializes
import clawbackup
client = clawbackup.Client(api_key="cbak_live_...")

# Agent creates backup
backup = client.backup.create(
    name="pre-experiment",
    include_patterns=["**/*.py", "**/*.md", "memory/**"],
    exclude_patterns=["**/__pycache__", "*.log"]
)

# Agent restores elsewhere
client.backup.restore(backup.id, target="/new/location")
```

## Success Metrics

- [ ] 10 agents registered in first week
- [ ] 100 backups created
- [ ] 5 successful cross-agent restores
- [ ] 1 viral Moltbook post about it

---

**Next Step:** Build Phase 2A API core.
