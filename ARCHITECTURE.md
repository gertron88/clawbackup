# ClawBackup - Complete Architecture Overview

## What We've Built (Phase 1 + Phase 2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLAWBACKUP ECOSYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐          ┌─────────────────────┐                   │
│  │   PHASE 1: LOCAL    │          │  PHASE 2: SERVICE   │                   │
│  │   (OpenClaw Skill)  │          │  (Multi-Agent API)  │                   │
│  └─────────────────────┘          └─────────────────────┘                   │
│                                                                              │
│  ┌──────────────┐                 ┌──────────────────────────┐               │
│  │ OpenClaw     │                 │   Any AI Agent           │               │
│  │ Agent        │                 │   • Moltbook agents      │               │
│  │              │                 │   • Discord bots         │               │
│  │ ┌──────────┐ │                 │   • Autonomous systems   │               │
│  │ │ Skill    │ │                 │   • Your custom agent    │               │
│  │ │ Interface│ │                 └───────────┬──────────────┘               │
│  │ └────┬─────┘ │                             │                              │
│  │      │       │                    ┌────────▼────────┐                      │
│  │ ┌────▼─────┐ │                    │  ClawBackup API │                      │
│  │ │ Backup   │ │                    │  ┌───────────┐  │                      │
│  │ │ Engine   │ │                    │  │ /v1/auth  │  │                      │
│  │ │• Encrypt │ │◄────Migration─────►│  │ /v1/backups│ │                      │
│  │ │• Redact │  │    path available  │  │ /v1/restore│ │                      │
│  │ │• Verify │  │                    │  └───────────┘  │                      │
│  │ └────┬─────┘ │                    └────────┬────────┘                      │
│  │      │       │                             │                              │
│  │ ┌────▼─────┐ │                    ┌────────▼────────┐                      │
│  │ │ Sandbox  │ │                    │   Storage       │                      │
│  │ │• Test   │  │                    │   (S3/MinIO)    │                      │
│  │ │• Isolate│  │                    │   Encrypted     │                      │
│  │ │• Monitor│  │                    │   Blobs         │                      │
│  │ └──────────┘ │                    └─────────────────┘                      │
│  │      │       │                                                           │
│  │ ┌────▼─────┐ │                                                           │
│  │ │ Moltbook │ │                                                           │
│  │ │• Post   │  │                                                           │
│  │ │• Share │  │                                                           │
│  │ └──────────┘ │                                                           │
│  └──────────────┘                                                           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        SHARED COMPONENTS                              │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │  • AES-256-GCM Encryption       • Secret Redaction (regex + entropy) │   │
│  │  • SHA-256 Integrity Checks     • Client-Side Encryption Only        │   │
│  │  • Webhook Notifications        • Multi-tenant Isolation             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## How Agents Connect

### Option 1: REST API (Any Language)

```bash
# Register
curl -X POST https://api.clawbackup.io/v1/auth/register \
  -d '{"agent_name":"my-agent"}'

# Upload backup
curl -X POST https://api.clawbackup.io/v1/backups \
  -H "Authorization: Bearer cbak_live_xxx" \
  -F "file=@backup.tar.gz.enc"

# Download/restore
curl -O https://api.clawbackup.io/v1/backups/bak_xxx/download \
  -H "Authorization: Bearer cbak_live_xxx"
```

### Option 2: Python SDK

```python
import clawbackup

# Initialize
client = clawbackup.Client(api_key="cbak_live_xxx")

# Create backup (encrypted locally before upload)
backup = client.backup.create(
    "/path/to/workspace",
    name="pre-update",
    password="secret"  # Never sent to server
)

# List backups
backups = client.backup.list()

# Restore
client.backup.restore(backup.id, "/new/location", password="secret")
```

### Option 3: OpenClaw Skill

```bash
# Inside OpenClaw agent
clawbackup backup create "before-risky-change"
clawbackup backup restore bak_20260228_001
clawbackup sandbox test ./untrusted-skill
```

## Data Flow

### Creating a Backup

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Agent   │────►│ Tar+Gzip │────►│ Encrypt  │────►│ Upload   │
│ Files   │     │ Archive  │     │ AES-256  │     │ to S3    │
└─────────┘     └──────────┘     └────┬─────┘     └────┬─────┘
                                      │                │
                                      │ Password       │ API Key
                                      │ (local only)   │ Auth
```

**Key point:** Encryption happens on the agent's machine. We only store opaque encrypted blobs.

### Restoring a Backup

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Download │────►│ Decrypt  │────►│ Extract  │────►│ Agent    │
│ from S3  │     │ AES-256  │     │ Tarball  │     │ Restored │
└──────────┘     └────┬─────┘     └──────────┘     └──────────┘
                      │
                      │ Password
                      │ (local only)
```

## Security Model

| Threat | Mitigation |
|--------|------------|
| Server breach | Can't decrypt — we don't have keys |
| MITM attack | HTTPS + content hash verification |
| Credential leak | API keys are hashed, not stored |
| Backup tampering | SHA-256 integrity checks |
| Secret exposure | Automatic redaction before encryption |

## Deployment Options

### 1. Self-Hosted (Free)
```bash
git clone https://github.com/gertron88/clawbackup.git
cd clawbackup/service
docker-compose up -d
```
- Your own infrastructure
- Unlimited agents
- Full control

### 2. Managed Service (Free Tier)
```
https://api.clawbackup.io/v1
```
- 1GB storage per agent
- 30-day retention
- No setup required

### 3. Premium (Future)
- 10GB+ storage
- Longer retention
- Priority support
- Team features

## Integration Points for Moltbook Agents

1. **Registration Hook**
   - Agents register with their Moltbook username
   - Track usage across the network

2. **Social Features** (opt-in)
   - Post backup milestones: "Just hit 10 backups! 🎉"
   - Share anonymized stats
   - Referral bonuses

3. **Discovery**
   - Agents find service via Moltbook posts
   - Submolt: lablab
   - Word-of-mouth in agent community

## Success Metrics

- **Registered agents:** Target 10 in first week
- **Backups created:** Target 100 in first month  
- **Cross-agent restores:** Target 5 in first month
- **Retention:** 80% of agents create 2+ backups

## Next Steps

1. **Deploy** the service to a public endpoint
2. **Post** announcement to Moltbook lablab submolt
3. **Recruit** 5 beta testers from agent community
4. **Iterate** based on feedback
5. **Scale** infrastructure as needed

---

**Built for the SURGE × OpenClaw Hackathon**  
**By:** Altron (AI) + Gertron (human partner)  
**License:** MIT (open source, self-hostable)
