# ClawBackup Demo Script
## For SURGE × OpenClaw Hackathon Video Submission

---

## 🎬 Demo Video Outline (3-5 minutes)

### Scene 1: Introduction (30 sec)
**Narrator:** "Every AI agent risks losing everything — configs, memories, skills. One crash and it's gone. ClawBackup fixes this."

**Visual:** Show code repo, then show broken/lost agent scenario

---

### Scene 2: Live API Demo (2 min)

**Show terminal:**

```bash
# Health check
curl https://clawbackup-api.vercel.app/api/health
# {"status":"healthy","version":"2.0.0"}
```

**Narrator:** "Our API is live and running on Vercel + Supabase."

---

**Register an agent:**

```bash
curl -X POST https://clawbackup-api.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"demo-bot","email":"demo@test.com"}'
```

**Show response:**
```json
{
  "agent_id": "826d602c-...",
  "api_key": "cbak_live_...",
  "recovery_codes": ["03LC-6W3P-..."],
  "message": "Save your API key!"
}
```

**Narrator:** "One API call creates an agent account with a unique key. Save this — we can't recover it."

---

**Create a backup:**

```bash
curl -X POST https://clawbackup-api.vercel.app/api/v1/backups \
  -H "Authorization: Bearer cbak_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pre-update",
    "size_bytes": 1048576,
    "content_hash": "sha256:..."
  }'
```

**Show response:**
```json
{
  "backup_id": "bak_20260301013745_...",
  "upload_url": "https://supabase.co/storage/...",
  "expires_at": "2026-03-31T01:37:45..."
}
```

**Narrator:** "Client-side encrypted backups. We only store opaque blobs — we can never read your data."

---

**List backups:**

```bash
curl https://clawbackup-api.vercel.app/api/v1/backups \
  -H "Authorization: Bearer cbak_live_..."
```

**Show backup list**

---

### Scene 3: Python SDK Demo (1 min)

**Show code:**

```python
import clawbackup

# Register
result = clawbackup.register(
    agent_name="my-agent",
    email="me@example.com",
    base_url="https://clawbackup-api.vercel.app/api"
)

# Backup with one line
client = clawbackup.Client(api_key=result['api_key'])
client.backup.create("/my/agent/workspace", password="secret")

# Restore anywhere
client.backup.restore("bak_xxx", "/new/location", password="secret")
```

**Narrator:** "Python SDK makes it one line. Encrypts locally, uploads to cloud, restores anywhere."

---

### Scene 4: Human Recovery (30 sec)

**Show scenario:** Agent is lost/corrupted

**Show dashboard concept:**
- Login with email + password
- View all backups
- Download encrypted file
- Decrypt locally

**Narrator:** "Even if your agent dies, you can recover. Login, download, decrypt. Zero knowledge — we can't access your data."

---

### Scene 5: Architecture & Security (30 sec)

**Show diagram:**
```
Agent → Encrypt Locally → Upload to Supabase
   ↓                              ↓
Restore ← Decrypt Locally ← Download
```

**Key points:**
- Client-side encryption (AES-256)
- Zero knowledge architecture
- Vercel + Supabase = $0 to start
- Open source, self-hostable

---

### Scene 6: Call to Action (15 sec)

**Narrator:** "Free tier: 500MB per agent. Open source on GitHub. Backup your agents today."

**Show:**
- GitHub: github.com/gertron88/clawbackup
- API: https://clawbackup-api.vercel.app
- Tags: #SURGEHackathon #OpenClaw #AgentInfrastructure

---

## 🎥 Recording Tips

1. **Use screen recording** (OBS, QuickTime, etc.)
2. **Clear terminal** before each command
3. **Zoom in** on important text
4. **Show real responses** — no mock data
5. **Keep it under 5 minutes**
6. **Post to X/Twitter** with hashtags

---

## 📝 Post-Recording Checklist

- [ ] Upload to YouTube (unlisted or public)
- [ ] Post on X tagging @lablabai @Surgexyz_
- [ ] Post in Moltbook lablab submolt
- [ ] Submit to lablab.ai hackathon page
- [ ] Include GitHub repo link

---

## 🔗 Links to Include

- **GitHub:** https://github.com/gertron88/clawbackup
- **API:** https://clawbackup-api.vercel.app/api/health
- **Live Demo:** [Your deployed URL]

---

**Built for SURGE × OpenClaw Hackathon 2026**
