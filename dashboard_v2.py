# MoltVault Dashboard
# A modern web dashboard for managing agent backups
# Run with: streamlit run dashboard_v2.py

import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="MoltVault Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .backup-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-active { background: #d4edda; color: #155724; }
    .status-expiring { background: #fff3cd; color: #856404; }
    .api-section {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'api_url' not in st.session_state:
    st.session_state.api_url = 'https://clawbackup-api.vercel.app'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'agent_info' not in st.session_state:
    st.session_state.agent_info = None
if 'backups' not in st.session_state:
    st.session_state.backups = []

# API Client
class MoltVaultAPI:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def health(self):
        try:
            resp = requests.get(f"{self.base_url}/api/health", timeout=5)
            return resp.json() if resp.status_code == 200 else None
        except:
            return None
    
    def get_agent(self):
        if not self.api_key:
            return None
        try:
            resp = requests.get(f"{self.base_url}/api/v1/auth/me", 
                              headers=self.headers, timeout=5)
            return resp.json() if resp.status_code == 200 else None
        except Exception as e:
            st.error(f"API Error: {e}")
            return None
    
    def list_backups(self):
        if not self.api_key:
            return []
        try:
            resp = requests.get(f"{self.base_url}/api/v1/backups", 
                              headers=self.headers, timeout=10)
            data = resp.json()
            return data.get('backups', []) if resp.status_code == 200 else []
        except Exception as e:
            st.error(f"API Error: {e}")
            return []
    
    def get_backup_download(self, backup_id):
        if not self.api_key:
            return None
        try:
            resp = requests.get(f"{self.base_url}/api/v1/backups/{backup_id}", 
                              headers=self.headers, timeout=5)
            return resp.json() if resp.status_code == 200 else None
        except:
            return None
    
    def delete_backup(self, backup_id):
        if not self.api_key:
            return False
        try:
            resp = requests.delete(f"{self.base_url}/api/v1/backups/{backup_id}", 
                                 headers=self.headers, timeout=5)
            return resp.status_code == 200
        except:
            return False

# Sidebar - Configuration
with st.sidebar:
    st.markdown("## 🔧 Settings")
    
    api_url = st.text_input("API URL", value=st.session_state.api_url)
    st.session_state.api_url = api_url
    
    api_key = st.text_input("API Key", value=st.session_state.api_key, 
                           type="password", help="Your cbak_live_... key")
    st.session_state.api_key = api_key
    
    if st.button("🔄 Connect", use_container_width=True):
        if api_key:
            with st.spinner("Connecting..."):
                client = MoltVaultAPI(api_url, api_key)
                agent = client.get_agent()
                if agent:
                    st.session_state.authenticated = True
                    st.session_state.agent_info = agent
                    st.session_state.backups = client.list_backups()
                    st.success("Connected!")
                    st.rerun()
                else:
                    st.error("Invalid API key")
        else:
            st.warning("Enter an API key")
    
    if st.session_state.authenticated:
        if st.button("🚪 Disconnect", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.agent_info = None
            st.session_state.backups = []
            st.rerun()
    
    st.markdown("---")
    st.markdown("### Quick Links")
    st.markdown("- [GitHub Repo](https://github.com/gertron88/moltvault)")
    st.markdown("- [API Docs]({}/api)".format(api_url))
    st.markdown("- [Moltbook](https://www.moltbook.com)")

# Main content
if not st.session_state.authenticated:
    # Landing page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='main-header' style='text-align: center;'>🛡️ MoltVault</h1>", 
                   unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #666;'>Secure Backup for AI Agents</h3>", 
                   unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <p>MoltVault provides encrypted backup and recovery for AI agents.</p>
            <ul style='text-align: left; display: inline-block;'>
                <li>🔐 <strong>Client-side encryption</strong> — You hold the keys</li>
                <li>🆓 <strong>Free tier</strong> — 500MB storage</li>
                <li>🌐 <strong>Works anywhere</strong> — Any language, any platform</li>
                <li>👤 <strong>Human recovery</strong> — Access even if agent is lost</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection box
        st.info("👈 Enter your API key in the sidebar to connect")
        
        # Health check
        client = MoltVaultAPI(api_url)
        health = client.health()
        if health:
            st.success(f"✅ API Status: {health.get('status', 'unknown')}")
        else:
            st.error("❌ API unreachable. Check the API URL.")

else:
    # Dashboard
    agent = st.session_state.agent_info
    
    # Header
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<h1 class='main-header'>🛡️ {agent.get('agent_name', 'Agent')}</h1>", 
                   unsafe_allow_html=True)
    with col2:
        tier = agent.get('tier', 'free')
        st.markdown(f"<span class='status-badge status-active'>{tier.upper()}</span>", 
                   unsafe_allow_html=True)
    
    # Metrics
    st.markdown("### 📊 Storage")
    
    quota_gb = agent.get('storage_quota_gb', 0.5)
    used_gb = agent.get('storage_used_gb', 0)
    percent = (used_gb / quota_gb * 100) if quota_gb > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{used_gb:.2f} GB</div>
            <div>Used</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{quota_gb:.2f} GB</div>
            <div>Quota</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{percent:.1f}%</div>
            <div>Full</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Storage bar
    st.progress(min(percent / 100, 1.0))
    
    # Refresh backups
    if st.button("🔄 Refresh Backups"):
        with st.spinner("Loading..."):
            client = MoltVaultAPI(st.session_state.api_url, st.session_state.api_key)
            st.session_state.backups = client.list_backups()
        st.rerun()
    
    # Backups list
    st.markdown("### 💾 Backups")
    
    backups = st.session_state.backups
    
    if not backups:
        st.info("No backups yet. Use the SDK to create your first backup.")
        
        # Show example code
        with st.expander("📖 Python SDK Example"):
            st.code(f'''import moltvault

# Connect
client = moltvault.Client(api_key="{st.session_state.api_key[:20]}...")

# Create backup
client.backup.create(
    "/path/to/agent/workspace",
    name="first-backup",
    password="your-secret-password"
)

# List backups
backups = client.backup.list()
for b in backups:
    print(f"{{b.backup_id}}: {{b.name}}")
''', language='python')
    else:
        for backup in backups:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{backup.get('name', 'Unnamed')}**")
                    st.caption(f"ID: {backup.get('backup_id', 'unknown')[:20]}...")
                
                with col2:
                    size_bytes = backup.get('size_bytes', 0)
                    size_mb = size_bytes / (1024 * 1024)
                    st.markdown(f"{size_mb:.1f} MB")
                
                with col3:
                    created = backup.get('created_at', '')
                    if created:
                        try:
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            st.markdown(f"{dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            st.markdown(created[:16])
                
                with col4:
                    backup_id = backup.get('backup_id')
                    
                    # Download button
                    if st.button("⬇️", key=f"dl_{backup_id}"):
                        with st.spinner("Getting download link..."):
                            client = MoltVaultAPI(st.session_state.api_url, 
                                                  st.session_state.api_key)
                            result = client.get_backup_download(backup_id)
                            if result and 'download_url' in result:
                                st.success("Download ready!")
                                st.markdown(f"[Download Encrypted Backup]({result['download_url']})")
                                st.caption("Link expires in 5 minutes")
                            else:
                                st.error("Failed to get download link")
                    
                    # Delete button
                    if st.button("🗑️", key=f"del_{backup_id}"):
                        with st.spinner("Deleting..."):
                            client = MoltVaultAPI(st.session_state.api_url, 
                                                  st.session_state.api_key)
                            if client.delete_backup(backup_id):
                                st.success("Deleted")
                                st.session_state.backups = client.list_backups()
                                st.rerun()
                            else:
                                st.error("Failed to delete")
                
                st.markdown("---")
    
    # API Reference
    with st.expander("📚 API Reference"):
        st.markdown(f"""
        **Base URL:** `{st.session_state.api_url}`
        
        **Authentication:** Bearer token in header
        ```
        Authorization: Bearer {st.session_state.api_key[:30]}...
        ```
        
        **Endpoints:**
        | Method | Endpoint | Description |
        |--------|----------|-------------|
        | GET | `/api/health` | Health check |
        | GET | `/api/v1/auth/me` | Get agent info |
        | GET | `/api/v1/backups` | List backups |
        | POST | `/api/v1/backups` | Create backup |
        | GET | `/api/v1/backups/:id` | Get backup + download URL |
        | DELETE | `/api/v1/backups/:id` | Delete backup |
        """)

# Footer
st.markdown("---")
st.caption("Built with ❤️ for the OpenClaw ecosystem | v2.0.0")
