# ClawBackup Service

Multi-agent backup service with client-side encryption. Any AI agent can register, backup their state, and restore anywhere.

## Quick Start

### 1. Start the Service

```bash
cd service
docker-compose up -d
```

This starts:
- API server on http://localhost:8000
- PostgreSQL database
- MinIO S3-compatible storage (console at http://localhost:9001)

### 2. Register Your Agent

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "my-awesome-agent",
    "moltbook_username": "@myagent"
  }'
```

Save the API key — it's shown only once!

### 3. Install the SDK

```bash
pip install -e service/sdk/python
```

### 4. Create a Backup

```python
import clawbackup

client = clawbackup.Client(api_key="cbak_live_...")

# One-liner backup
backup = client.backup.create(
    "/path/to/agent/workspace",
    name="pre-update",
    password="my-secret-password"
)

print(f"Backup created: {backup.id}")
```

### 5. Restore Anywhere

```python
# On another machine
client = clawbackup.Client(api_key="cbak_live_...")

client.backup.restore(
    backup_id="bak_abc123...",
    target_path="/new/location",
    password="my-secret-password"
)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Register new agent |
| GET | `/v1/auth/me` | Get agent info |
| POST | `/v1/backups` | Upload backup |
| GET | `/v1/backups` | List backups |
| GET | `/v1/backups/:id` | Get backup metadata |
| GET | `/v1/backups/:id/download` | Download backup |
| DELETE | `/v1/backups/:id` | Delete backup |

## Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Agent A   │◄────►│  ClawBackup │◄────►│   Agent B   │
│  ( anywhere)│      │   Service   │      │  (anywhere) │
└─────────────┘      └──────┬──────┘      └─────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │PostgreSQL│   │  MinIO  │   │  Redis  │
        │(metadata)│   │(backups)│   │(queues) │
        └─────────┘   └─────────┘   └─────────┘
```

## Security

- **Client-side encryption**: We never see your data
- **Encrypted at rest**: Using your encryption key
- **Integrity verification**: SHA-256 hashes on all backups
- **API key auth**: Unique keys per agent

## Environment Variables

```bash
CLAWBACKUP_DATABASE_URL=postgresql://...     # Database connection
CLAWBACKUP_S3_ENDPOINT=http://localhost:9000 # MinIO/S3 endpoint
CLAWBACKUP_S3_BUCKET=clawbackup              # Bucket name
CLAWBACKUP_S3_ACCESS_KEY=minioadmin          # S3 credentials
CLAWBACKUP_S3_SECRET_KEY=minioadmin          # S3 credentials
CLAWBACKUP_FREE_TIER_QUOTA_GB=1.0            # Quota per agent
CLAWBACKUP_BACKUP_RETENTION_DAYS=30          # Auto-cleanup
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn api.main:app --reload

# Run tests
pytest tests/
```

## Production Deployment

For production, update:

1. **Use real S3** instead of MinIO
2. **Use managed PostgreSQL** (RDS, Cloud SQL, etc.)
3. **Add SSL/TLS** (Let's Encrypt)
4. **Rate limiting** (Redis-based)
5. **Monitoring** (Prometheus/Grafana)

## License

MIT
