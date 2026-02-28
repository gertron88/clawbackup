# ClawBackup Vercel + Supabase Deployment

## Quick Deploy

### 1. Create Supabase Project
1. Go to https://supabase.com
2. Create new project
3. Save your **Project URL** and **Service Role Key**

### 2. Run SQL Setup
1. Go to SQL Editor in Supabase Dashboard
2. Copy contents of `supabase-setup.sql`
3. Run the SQL

### 3. Create Storage Bucket
1. Go to Storage in Supabase Dashboard
2. Create new bucket named `backups`
3. Set to **Private** (access controlled via API)

### 4. Deploy to Vercel
```bash
cd vercel-api

# Install Vercel CLI if needed
npm i -g vercel

# Login
vercel login

# Set environment variables
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY

# Deploy
vercel --prod
```

### 5. Test the API
```bash
# Health check
curl https://your-api.vercel.app/health

# Register agent
curl -X POST https://your-api.vercel.app/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "test-agent", "email": "you@example.com", "password": "secret123"}'

# Save the API key from response!
```

## Environment Variables

| Variable | Where to Get |
|----------|--------------|
| `SUPABASE_URL` | Supabase Dashboard → Settings → API → URL |
| `SUPABASE_SERVICE_KEY` | Supabase Dashboard → Settings → API → service_role key |
| `SUPABASE_ANON_KEY` | Supabase Dashboard → Settings → API → anon/public key |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Create agent account |
| POST | `/v1/auth/login` | Human dashboard login |
| GET | `/v1/auth/me` | Get agent info |
| GET | `/v1/backups` | List backups |
| POST | `/v1/backups` | Create backup (get upload URL) |
| GET | `/v1/backups/[id]` | Get download URL |
| DELETE | `/v1/backups/[id]` | Delete backup |
| GET | `/health` | Health check |

## SDK Usage

```python
import clawbackup

# Register (one time)
# curl -X POST .../v1/auth/register

# Use
client = clawbackup.Client(
    api_key="cbak_live_...",
    base_url="https://your-api.vercel.app"
)

# Backup
backup = client.backup.create("/path", password="secret")

# Restore
client.backup.restore(backup.id, "/new/path", password="secret")
```

## Free Tier Limits

- **Supabase:** 500MB database, 1GB storage
- **Vercel:** 100GB bandwidth, 10s function timeout
- **Our limits:** 500MB per agent, 30-day retention

## Human Recovery Flow

1. Go to dashboard (build separately or use API)
2. Login with email/password
3. View all backups
4. Download encrypted file
5. Decrypt locally with backup password

```bash
# Download via API
curl https://your-api.vercel.app/v1/backups/bak_xxx \
  -H "Authorization: Bearer cbak_live_..." \
  | jq -r '.download_url' \
  | xargs curl -o backup.enc

# Decrypt locally (Python SDK or standalone script)
python3 -c "
import clawbackup
clawbackup.decrypt_file('backup.enc', 'backup.tar.gz', password='secret')
"
```

## Troubleshooting

**CORS errors:** API sets `Access-Control-Allow-Origin: *` - should work everywhere

**Upload fails:** Check Supabase Storage bucket exists and is private

**Auth fails:** Verify API key format starts with `cbak_live_`

**Large files:** Vercel has 4.5MB body limit - use signed URLs for direct-to-storage upload
