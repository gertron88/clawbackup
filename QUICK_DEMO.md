# Quick Demo Commands for Video

## 30-Second Demo

```bash
# 1. Health check
curl https://clawbackup-api.vercel.app/api/health

# 2. Register agent
curl -X POST https://clawbackup-api.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"demo-agent","email":"demo@test.com"}'

# 3. Create backup (using API key from step 2)
curl -X POST https://clawbackup-api.vercel.app/api/v1/backups \
  -H "Authorization: Bearer cbak_live_..." \
  -H "Content-Type: application/json" \
  -d '{"name":"my-backup","size_bytes":1024}'

# 4. List backups
curl https://clawbackup-api.vercel.app/api/v1/backups \
  -H "Authorization: Bearer cbak_live_..."
```

## Full Feature Demo

```bash
# Register with all fields
curl -X POST https://clawbackup-api.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "production-bot",
    "email": "admin@company.com",
    "moltbook_username": "@mybot",
    "password": "dashboard-password"
  }'

# Create backup with tags
curl -X POST https://clawbackup-api.vercel.app/api/v1/backups \
  -H "Authorization: Bearer cbak_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pre-deployment-v2",
    "tags": ["stable", "production"],
    "size_bytes": 5242880,
    "content_hash": "sha256:..."
  }'
```

## Python SDK Demo

```python
# Install
pip install clawbackup-agent

# Quick backup
import clawbackup

# Register (one time)
result = clawbackup.register(
    agent_name="my-agent",
    email="me@example.com",
    base_url="https://clawbackup-api.vercel.app/api"
)
print(f"API Key: {result['api_key']}")

# Use it
client = clawbackup.Client(api_key=result['api_key'])

# Create backup (encrypted locally)
backup = client.backup.create(
    "/my/agent/workspace",
    name="pre-update",
    password="my-secret-password"
)
print(f"Backup created: {backup.id}")

# List backups
backups = client.backup.list()
for b in backups:
    print(f"  - {b.name} ({b.size_bytes} bytes)")
```

## Recovery Demo

```bash
# Human logs in
curl -X POST https://clawbackup-api.vercel.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"dashboard-password"}'

# Get download URL
curl https://clawbackup-api.vercel.app/api/v1/backups/bak_xxx \
  -H "Authorization: Bearer cbak_live_..."

# Download and decrypt locally
python3 -c "
import clawbackup
clawbackup.decrypt_backup('backup.enc', 'backup.tar.gz', password='my-secret-password')
"
```

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Your Agent  │────►│   Encrypt    │────►│  Supabase       │
│ Anywhere    │     │   (Local)    │     │  (Encrypted)    │
└─────────────┘     └──────────────┘     └─────────────────┘
       │                                            │
       │ Restore Anywhere                           │
       ▼                                            ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ New Agent   │◄────│   Decrypt    │◄────│  Human Download │
│ Instance    │     │   (Local)    │     │  (If agent dies)│
└─────────────┘     └──────────────┘     └─────────────────┘
```

**Key Features:**
- ✅ Client-side encryption (AES-256)
- ✅ Zero knowledge (we can't read your data)
- ✅ Free tier: 500MB per agent
- ✅ Open source, self-hostable

**Links:**
- API: https://clawbackup-api.vercel.app/api/health
- GitHub: https://github.com/gertron88/clawbackup
