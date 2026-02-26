# Streamlit Cloud Deployment Configuration

## Deploy via Web UI (Recommended)

1. Go to: https://share.streamlit.io/
2. Click "New app"
3. Select repository: `gertron88/clawbackup`
4. Main file path: `web/dashboard.py`
5. Click "Deploy"

## Deploy via Streamlit CLI

```bash
# Install Streamlit
pip install streamlit

# Login to Streamlit Cloud
streamlit login

# Deploy
streamlit deploy web/dashboard.py
```

## Configuration

The app requires these secrets (set in Streamlit Cloud UI):
- `CLAWBACKUP_PASSWORD` - Encryption password
- `MOLTBOOK_API_KEY` - Optional, for live posting

## App URL Pattern

Once deployed: `https://clawbackup-{username}.streamlit.app`

## Files Deployed

- `web/dashboard.py` - Main dashboard
- `skill/backup_engine.py` - Backup logic
- `skill/sandbox.py` - Sandbox testing
- `requirements.txt` - Dependencies
