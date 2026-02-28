# ClawBackup Deployment Guide

## Deploy from GitHub to Vercel (Easiest Method)

### Step 1: Go to Vercel
Visit: https://vercel.com/new

### Step 2: Import Your Repo
1. Click **"Import Git Repository"**
2. Select: **gertron88/clawbackup**
3. Click **Import**

### Step 3: Configure Project

**Project Name:** `clawbackup` (or your preference)

**Framework Preset:** `Other` (or leave as detected)

**Root Directory:** `./` (default - repository root)

**Build Command:** (leave empty - not needed for API routes)

**Output Directory:** (leave empty)

**Install Command:** `npm install`

### Step 4: Add Environment Variables

Click **"Environment Variables"** and add:

| Name | Value |
|------|-------|
| `SUPABASE_URL` | `https://ysrgejrwstsxqhtopmcy.supabase.co` |
| `SUPABASE_SERVICE_KEY` | `sb_secret_...` (get from Supabase dashboard) |

### Step 5: Deploy
Click **"Deploy"**

Wait 1-2 minutes for build to complete.

### Step 6: Get Your URL

After deployment succeeds, you'll see a URL like:
```
https://clawbackup-abc123.vercel.app
```

**Copy this URL and give it to me for testing.**

---

## Alternative: Vercel CLI with Token

If you prefer CLI, create a token:

1. Go to: https://vercel.com/account/tokens
2. Click **"Create Token"**
3. Name: `clawbackup-deploy`
4. Scope: Select your team/personal account
5. Copy the token
6. Give it to me

I'll run:
```bash
vercel --token YOUR_TOKEN --prod
```

---

## Post-Deploy: Supabase Setup

After deployment, you MUST run the SQL setup:

1. Go to https://supabase.com
2. Select project: **ysrgejrwstsxqhtopmcy**
3. Go to **SQL Editor**
4. Copy contents of `supabase-setup.sql` from your repo
5. Click **Run**

Then create storage bucket:
1. Go to **Storage**
2. Click **New Bucket**
3. Name: `backups`
4. Set to **Private**
5. Click **Save**

---

## Test the Deployment

Once deployed and configured, test with:

```bash
# Health check
curl https://your-url.vercel.app/health

# Should return:
# {"status":"healthy","version":"2.0.0",...}
```

Give me your deployment URL when ready!
