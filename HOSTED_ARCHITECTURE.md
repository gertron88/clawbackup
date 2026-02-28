# ClawBackup Hosted Architecture
## Using Vercel + Supabase (What Gert Has)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOSTED CLAWBACKUP SERVICE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────┐        ┌───────────────────┐        ┌──────────────┐ │
│  │   Vercel          │        │   Supabase        │        │  Supabase    │ │
│  │   (Edge/API)      │        │   (PostgreSQL)    │        │  Storage     │ │
│  │                   │        │                   │        │  (S3-compat) │ │
│  │ ┌─────────────┐   │        │ ┌─────────────┐   │        │ ┌──────────┐ │ │
│  │ │ API Routes  │   │◄──────►│ │ agents      │   │        │ │ Encrypted│ │ │
│  │ │ /v1/auth/*  │   │        │ │ backups     │   │◄───────│ │ Backups  │ │ │
│  │ │ /v1/backups/*│  │        │ │ webhooks    │   │        │ │ (blobs)  │ │ │
│  │ └─────────────┘   │        │ └─────────────┘   │        │ └──────────┘ │ │
│  │        │          │        └───────────────────┘        └──────────────┘ │
│  │        │          │                                                      │
│  │ ┌──────▼──────┐   │                                                      │
│  │ │ Middleware  │   │                                                      │
│  │ │• Rate limit │   │                                                      │
│  │ │• CORS       │   │                                                      │ │
│  │ └─────────────┘   │                                                      │
│  └───────────────────┘                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

ENCRYPTION FLOW (Client-Side Only):

┌──────────┐     ┌──────────┐     ┌──────────┐     ┌────────────────────────┐
│ Agent    │────►│ Encrypt  │────►│ Upload   │────►│ Supabase Storage       │
│ Files    │     │ (local)  │     │ (blob)   │     │ AES-256 encrypted blob │
└──────────┘     └────┬─────┘     └──────────┘     └────────────────────────┘
                      │
                      │ Password NEVER leaves agent
```

## Why This Works

| Component | Why | Limits |
|-----------|-----|--------|
| **Vercel** | Edge functions, auto-scaling, free tier | 10s execution (Hobby), 50MB payload |
| **Supabase DB** | PostgreSQL, row-level security, free tier | 500MB database |
| **Supabase Storage** | S3-compatible, CDN, free tier | 1GB storage |

## Domain Setup

Yes, you need a domain:
- **Primary:** `api.clawbackup.io` → Vercel
- **Dashboard:** `app.clawbackup.io` → Vercel (or same domain)

Free options if you don't have one:
- `clawbackup.vercel.app` (free Vercel subdomain)
- `clawbackup.supabase.co` (Supabase subdomain for storage)

## Human Recovery Flow (When Agent Dies)

### Scenario 1: Agent Lost, Human Has Backup Password

```
┌──────────┐     ┌─────────────────────┐     ┌──────────────────┐
│ Human    │────►│ Web Dashboard       │────►│ Download         │
│          │     │ app.clawbackup.io   │     │ Encrypted Blob   │
│          │     │                     │     │                  │
│          │     │ 1. Login with       │     │ ↓                │
│          │     │    email/password   │     │ Decrypt locally  │
│          │     │                     │     │ ↓                │
│          │     │ 2. View backups     │     │ Extract tar.gz   │
│          │     │    by agent name    │     │ ↓                │
│          │     │                     │     │ Full restore!    │
│          │     │ 3. Download any     │     │                  │
│          │     │    backup file      │     │                  │
└──────────┘     └─────────────────────┘     └──────────────────┘
```

### Scenario 2: Restore to New Agent

```python
# New agent spins up
import clawbackup

# Human provides API key from dashboard
client = clawbackup.Client(api_key="cbak_live_...")

# Download and restore
client.backup.restore("bak_xxx", "/new/agent/path", password="secret")
```

## Authentication Options

### Option A: Dual Auth (Recommended)

**Agent Auth:** API Key (`cbak_live_xxx`)
- For automated backups from running agents
- Stored in agent environment

**Human Auth:** Email + Password
- For dashboard access
- Recovery when agent is lost
- Can download encrypted files directly

### Database Schema (Supabase)

```sql
-- Agents table (both agent and human access)
create table agents (
    id uuid primary key default gen_random_uuid(),
    agent_name text unique not null,
    moltbook_username text,
    
    -- Agent auth
    api_key_hash text unique not null,  -- For API calls
    
    -- Human auth (for dashboard/recovery)
    email text,
    password_hash text,  -- bcrypt hashed
    
    -- Recovery
    recovery_codes jsonb default '[]',
    
    -- Limits
    tier text default 'free',
    storage_quota_gb float default 0.5,
    storage_used_gb float default 0,
    
    created_at timestamp default now()
);

-- Backups table
create table backups (
    id uuid primary key default gen_random_uuid(),
    backup_id text unique not null,  -- Human readable: bak_xxx
    agent_id uuid references agents(id) on delete cascade,
    
    name text not null,
    size_bytes integer not null,
    content_hash text not null,  -- SHA-256 of encrypted blob
    
    -- Storage location in Supabase
    storage_bucket text default 'backups',
    storage_path text not null,  -- path in bucket
    
    tags text[] default '{}',
    created_at timestamp default now(),
    expires_at timestamp not null,
    
    -- For soft delete (grace period)
    deleted_at timestamp
);

-- Row Level Security (critical!)
alter table agents enable row level security;
alter table backups enable row level security;

-- Agents can only see their own data
create policy "Agents access own data" on agents
    for all using (auth.uid()::text = id::text);
    
create policy "Backups belong to agent" on backups
    for all using (agent_id in (
        select id from agents where auth.uid()::text = id::text
    ));
```

## Vercel API Routes Structure

```
api/
├── _lib/
│   ├── supabase.ts      # Supabase client
│   ├── auth.ts          # Auth helpers
│   └── encryption.ts    # Client-side encryption utils
├── v1/
│   ├── auth/
│   │   ├── register.ts  # POST - create agent
│   │   ├── login.ts     # POST - human login
│   │   └── me.ts        # GET - current agent info
│   ├── backups/
│   │   ├── index.ts     # GET list, POST create
│   │   └── [id].ts      # GET download, DELETE
│   └── health.ts        # GET health check
└── dashboard/
    ├── login.ts         # Human login
    └── backups.ts       # List backups for UI
```

## Cost Estimate (Supabase + Vercel)

| Tier | Supabase | Vercel | Total |
|------|----------|--------|-------|
| **Free** | $0 (500MB DB, 1GB storage) | $0 (100GB bandwidth) | **$0** |
| **Launch** | $25 (8GB DB, 100GB storage) | $20 (Pro) | **$45/mo** |
| **Scale** | $100+ | $100+ | **$200+/mo** |

## Implementation Priority

1. **Week 1:** Vercel + Supabase setup, basic auth
2. **Week 2:** Backup upload/download API
3. **Week 3:** Human dashboard (email/password login)
4. **Week 4:** Recovery codes, testing

## Key Decision: Do We Need Client-Side Encryption?

**YES - absolutely.** Here's why:

Without client-side encryption:
- Supabase Storage stores plaintext
- We could read agent data
- Subpoena = data exposed
- Trust required

With client-side encryption:
- Supabase stores opaque blobs
- We CANNOT read data even if we wanted to
- Human downloads blob + decrypts locally
- Zero trust architecture

**Trade-off:** Human must remember backup password. No "password reset" for backups.

## Recovery Code System (for when human forgets password)

```
On registration:
1. Generate 10 recovery codes
2. Show ONCE to human
3. Store hashed in database

If human forgets password:
1. Provide email + recovery code
2. We verify code hash
3. Allow setting new password
4. Invalidate used recovery code

Note: Can't recover backup data without original password!
      Recovery codes only for dashboard access.
```

## Summary

| Question | Answer |
|----------|--------|
| **Domain needed?** | Yes, or use vercel.app subdomain |
| **Vercel works?** | Yes for API, but 10s limit on Hobby |
| **Supabase works?** | Yes - DB + Storage in one |
| **Auto-encryption?** | No - must be client-side, agent encrypts |
| **Human recovery?** | Yes - email/password dashboard + download |
| **Cost to start?** | $0 on free tiers |
| **Backup size limit?** | ~4GB (Supabase max per file) |

**Next step:** Set up Supabase project, configure storage bucket, deploy Vercel API.
