# 🛡️ ClawBackup

**Multi-agent backup service with client-side encryption.**

Any AI agent can backup their state, restore anywhere, and recover even if the original agent is lost. Built for the SURGE × OpenClaw Hackathon.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/gertron88/clawbackup)

---

## 🎯 What It Does

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

**Key features:**
- 🔐 **Client-side encryption** — We never see your data
- 🆓 **Free tier** — 500MB storage per agent  
- 🌐 **Works anywhere** — Any language, any platform
- 👤 **Human recovery** — Download backups if agent is lost
- 🚀 **Auto-deploy** — Vercel + Supabase = $0 to start

---

## 🚀 Quick Start

### For Agents (Python SDK)

```python
import clawbackup

# 1. Register (one time)
result = clawbackup.register(
    agent_name="my-agent",
    email="you@example.com",      # For human recovery
    password="dashboard-pass"     # For human recovery
)
# SAVE: result['api_key'] and result['recovery_codes']

# 2. Backup
client = clawbackup.Client(api_key="cbak_live_...")
client.backup.create("/agent/workspace", password="backup-secret")

# 3. Restore
client.backup.restore("bak_xxx", "/new/location", password="backup-secret")
```

### For Humans (Recovery)

If the agent is lost:

```bash
# 1. Login to dashboard (or use API directly)
curl -X POST https://your-app.vercel.app/v1/auth/login \
  -d '{"email":"you@example.com","password":"dashboard-pass"}'

# 2. List backups
curl https://your-app.vercel.app/v1/backups \
  -H "Authorization: Bearer cbak_live_..."

# 3. Download encrypted backup
curl -O https://.../download \
  -H "Authorization: Bearer cbak_live_..."

# 4. Decrypt locally (you need the backup password)
python3 -c "
import clawbackup
clawbackup.decrypt_backup('backup.enc', 'backup.tar.gz', password='backup-secret')
"
```

---

## 🏗️ Deploy Your Own (Free)

### 1. Fork & Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/gertron88/clawbackup)

Or manually:
```bash
# Clone
git clone https://github.com/gertron88/clawbackup.git
cd clawbackup

# Install
npm install

# Set environment variables (see below)
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY

# Deploy
vercel --prod
```

### 2. Set Up Supabase

1. Create project at [supabase.com](https://supabase.com)
2. Run SQL in [supabase-setup.sql](./supabase-setup.sql)
3. Create a **private** storage bucket named `backups`
4. Copy URL and service role key to Vercel env vars

### 3. Test

```bash
curl https://your-app.vercel.app/health
# → {"status":"healthy"}
```

**Cost:** $0 (Vercel + Supabase free tiers)

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | - | Health check |
| POST | `/v1/auth/register` | - | Create agent account |
| POST | `/v1/auth/login` | - | Human dashboard login |
| GET | `/v1/auth/me` | API Key | Get agent info |
| GET | `/v1/backups` | API Key | List backups |
| POST | `/v1/backups` | API Key | Create backup (get upload URL) |
| GET | `/v1/backups/:id` | API Key | Get download URL |
| DELETE | `/v1/backups/:id` | API Key | Delete backup |

---

## 🔐 Security Model

| Threat | Mitigation |
|--------|------------|
| Server breach | Can't decrypt — we don't have keys |
| Database leak | Only encrypted blobs stored |
| MITM attack | HTTPS + content hash verification |
| Insider threat | Zero knowledge — we can't read data |

**Important:** We cannot recover backup data if you forget the backup password. Store it safely (e.g., password manager).

---

## 💾 Storage Limits

| Tier | Storage | Retention | Price |
|------|---------|-----------|-------|
| **Free** | 500MB | 30 days | **$0** |
| Pro | 5GB | 90 days | $5/mo |
| Team | 50GB | 1 year | $29/mo |

**Realistic usage:**
- Light agent: ~5MB/backup → ~100 backups free
- Medium agent: ~20MB/backup → ~25 backups free
- Heavy agent: ~100MB/backup → ~5 backups free

---

## 🛠️ Project Structure

```
clawbackup/
├── api/                    # Vercel API routes
│   ├── v1/
│   │   ├── auth/          # Registration, login
│   │   └── backups/       # Backup CRUD
│   └── _lib/              # Shared utilities
├── sdk/
│   └── clawbackup.py      # Python SDK
├── supabase-setup.sql     # Database schema
├── package.json           # Node deps
├── tsconfig.json          # TypeScript config
└── vercel.json            # Vercel config
```

---

## 📚 Documentation

- [Architecture](./ARCHITECTURE.md) — System design
- [Hosted Architecture](./HOSTED_ARCHITECTURE.md) — Vercel + Supabase details
- [Moltbook Launch](./MOLTBOOK_LAUNCH.md) — Marketing copy
- [Phase 2 Summary](./PHASE2_SUMMARY.md) — Implementation notes

---

## 🏆 Hackathon

Built for **SURGE × OpenClaw Hackathon** (March 1, 2026)

**Tracks:** Developer Infrastructure & Tools + Autonomous Payments

---

## 📄 License

MIT — See [LICENSE](./LICENSE)

**Built by:** Altron (AI) + Gertron (human partner)  
**GitHub:** [github.com/gertron88/clawbackup](https://github.com/gertron88/clawbackup)

---

*Protect your agents. Preserve your work. Build with confidence.* 🛡️
