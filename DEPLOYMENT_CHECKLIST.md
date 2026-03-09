# 🚀 MoltVault Production Deployment Checklist

**Project:** MoltVault (formerly ClawBackup)  
**Status:** Rebranded for public release - ClawBackup was the internal codename  
**Status:** Code Complete → Production Pending  
**Deadline:** ASAP (Gert leaves for Albania March 2)

---

## ✅ Completed (March 6, 2026)

### Code & Architecture
- [x] API routes (health, auth, backups)
- [x] TypeScript compilation passing
- [x] Supabase schema defined
- [x] SDK structure ready
- [x] Documentation complete
- [x] **API Routing Fixed** - All endpoints now accessible
- [x] **Deployment Script Created** - `deploy.sh` handles Vercel auth
- [x] **Dashboard v2 Created** - Real API connection

### Infrastructure
- [x] Vercel CLI installed (v50.25.4)
- [x] Node dependencies installed
- [x] Git repository initialized
- [x] Vercel project exists (`prj_sb1L56HlK6ddoFvbTrI3tXDpWxW5`)

---

## ⏳ Required for Production

### 1. Vercel Authentication
**Status:** NOT CONFIGURED

**Options:**
- A) `vercel login` (requires browser - do this manually)
- B) Use Vercel token via `--token` flag

**Action Required:**
```bash
# Option A (Interactive):
vercel login
# → Opens browser, authenticate with GitHub

# Option B (Token-based, for CI/CD):
vercel --token <VERCEL_TOKEN> --prod
```

### 2. Supabase Project Setup
**Status:** NOT CREATED

**Steps:**
1. Go to https://supabase.com
2. Create new project
3. Name: `moltvault-production`
4. Region: Pick closest to users (US East recommended)
5. Save the following:
   - Project URL: `SUPABASE_URL`
   - Service Role Key: `SUPABASE_SERVICE_KEY` (NOT anon key!)

**SQL Setup:**
Run the contents of `supabase-setup.sql` in Supabase SQL Editor

**Storage Setup:**
1. Go to Storage → Buckets
2. Create bucket named `backups`
3. Set to PRIVATE
4. Configure RLS policies (see supabase-setup.sql)

### 3. Environment Variables

**Set in Vercel Dashboard:**
```bash
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service-role-key>
```

Or via CLI:
```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
```

### 4. Deploy to Production

```bash
cd ~/.openclaw/workspace/hackathons/clawbackup

# Verify build
npm run lint

# Deploy
vercel --prod

# Or with token
vercel --token $VERCEL_TOKEN --prod
```

### 5. Post-Deploy Verification

```bash
# Health check
curl https://<your-domain>/api/health

# Should return:
# {"status":"healthy","version":"2.0.0",...}

# Test registration
curl -X POST https://<your-domain>/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"test-agent"}'
```

---

## 🔐 Credentials Needed from Gert

| Service | Credential | Status | Where to Find |
|---------|-----------|--------|---------------|
| Vercel | Token or login | ❌ Needed | https://vercel.com/account/tokens |
| Supabase | Project URL + Service Key | ❌ Needed | Supabase Dashboard → Settings → API |
| GitHub | PAT for repo push | ❌ Needed | GitHub Settings → Developer → Tokens |

---

## 📋 Quick Commands Summary

```bash
# 1. Install deps (DONE)
cd ~/.openclaw/workspace/hackathons/clawbackup
npm install

# 2. Auth Vercel (NEEDED)
vercel login
# OR use existing token

# 3. Set env vars (NEEDED)
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY

# 4. Deploy (NEEDED)
vercel --prod

# 5. Verify
curl https://your-app.vercel.app/api/health
```

---

## ⚠️ Blockers

1. **Vercel Auth** - Requires manual login or token
2. **Supabase Project** - Needs new project creation
3. **GitHub Push** - Repo exists locally, need to push to remote

---

## 🎯 Next Actions

**Gert to complete before Albania:**
1. [ ] Run `vercel login` in terminal
2. [ ] Create Supabase project, get credentials
3. [ ] Add env vars via `vercel env add`
4. [ ] Run `vercel --prod` to deploy
5. [ ] Test with curl commands above

**Estimated time:** 15-20 minutes

---

## 📁 File Locations

- **Project:** `~/.openclaw/workspace/hackathons/clawbackup/`
- **API:** `api/index.ts`
- **SQL:** `supabase-setup.sql`
- **SDK:** `sdk/moltvault.py`
- **Docs:** `README.md`, `ARCHITECTURE.md`

---

Created: 2026-03-01  
By: Altron
