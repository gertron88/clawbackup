# ClawBackup Hosted Solution - Summary

## What You Need to Deploy

### 1. Domain (Optional but Recommended)
- **Free:** Use `clawbackup.vercel.app` (Vercel provides this)
- **Custom:** Buy a domain (e.g., `clawbackup.io` ~$12/year)

### 2. Supabase Account (Free)
- Sign up at https://supabase.com
- Create a project
- You get: 500MB PostgreSQL + 1GB Storage for free

### 3. Vercel Account (Free)
- Sign up at https://vercel.com  
- Connect GitHub repo
- Deploy with one click

**Total cost to start: $0**

---

## Architecture

```
Agent (anywhere) → Vercel Edge → Supabase DB + Storage
                        ↓
                  Encrypted blobs
                  (we can't read them)
```

**Key points:**
- **Client-side encryption:** Data encrypted on agent's machine before upload
- **Zero knowledge:** We store only opaque encrypted blobs
- **Human recovery:** Email/password login to dashboard for manual download

---

## Human Recovery Flow (When Agent Dies)

```
1. Human goes to dashboard (or uses API directly)
   URL: https://your-api.vercel.app/v1/auth/login

2. Login with email + password (set during registration)

3. View all backups for that agent

4. Download encrypted backup file:
   GET /v1/backups/bak_xxx → returns download URL
   
5. Decrypt locally (human must remember backup password):
   ```python
   import clawbackup
   clawbackup.decrypt_backup('backup.enc', 'backup.tar.gz', password='secret')
   ```

6. Extract and restore:
   ```bash
   tar -xzf backup.tar.gz -C /new/agent/location
   ```
```

**Important:** We cannot recover backup data if human forgets the backup password. We only store the encrypted blob.

---

## File Sizes (Realistic)

| Agent Type | Backup Size | Monthly Growth |
|------------|-------------|----------------|
| Light (chatbot) | 2-5MB | ~10MB/month |
| Medium (trading bot) | 10-20MB | ~50MB/month |
| Heavy (multi-project) | 50-100MB | ~200MB/month |

**Free tier (500MB/agent):**
- Light agent: ~100 backups
- Medium agent: ~25 backups  
- Heavy agent: ~5 backups

**Proposed paid tier ($5/month):**
- 5GB storage = 50-250 more backups

---

## Quick Start (Deploy in 10 Minutes)

```bash
# 1. Clone and enter
cd hackathons/clawbackup/vercel-api

# 2. Install dependencies
npm install

# 3. Set up Supabase
# - Create project at supabase.com
# - Run SQL from supabase-setup.sql
# - Create 'backups' storage bucket

# 4. Deploy to Vercel
vercel login
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
vercel --prod

# 5. Test
curl https://your-app.vercel.app/health
```

---

## SDK for Agents

```python
import clawbackup

# Register (one time, save API key!)
result = clawbackup.register(
    agent_name="my-trading-bot",
    email="you@example.com",      # For human recovery
    password="dashboard-password" # For human recovery
)
# Save: result['api_key'] and result['recovery_codes']

# Use
client = clawbackup.Client(api_key="cbak_live_...")

# Backup (encrypted locally before upload)
backup = client.backup.create("/agent/workspace", password="backup-secret")

# Restore
client.backup.restore(backup.id, "/new/location", password="backup-secret")
```

---

## Key Security Properties

| Question | Answer |
|----------|--------|
| Can you read agent backups? | **No** - encrypted client-side |
| Can you recover lost passwords? | **No** - zero knowledge |
| What if Supabase is breached? | **Safe** - only encrypted blobs |
| What if Vercel is compromised? | **Safe** - no decryption keys |
| Can human recover without agent? | **Yes** - via email + backup password |

---

## Monetization Path

| Tier | Storage | Price | Notes |
|------|---------|-------|-------|
| Free | 500MB | $0 | Bootstrap adoption |
| Pro | 5GB | $5/mo | Power users |
| Team | 50GB | $29/mo | Organizations |
| Enterprise | Unlimited | Custom | SLAs, support |

---

## Next Steps

1. **Deploy:** Set up Supabase + Vercel (30 min)
2. **Test:** Create agent, backup, restore (15 min)
3. **Announce:** Post to Moltbook lablab submolt (15 min)
4. **Iterate:** Get feedback from 3-5 beta testers

**Ready to go live?** The infrastructure is here. Just need to deploy.
