import streamlit as st
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="ClawBackup Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    .main-header {
        font-size: 3rem !important;
        font-weight: 700 !important;
        color: #1f77b4 !important;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .feature-box {
        background: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .security-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .demo-banner {
        background: #ffc107;
        color: #000;
        padding: 0.5rem;
        text-align: center;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.demo_mode = True

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='main-header' style='text-align: center;'>🛡️ ClawBackup</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #666;'>Backup & Recovery for OpenClaw Agents</h3>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Feature highlights
            cols = st.columns(3)
            with cols[0]:
                st.markdown("""
                <div class='feature-box'>
                <h4>🔐 AES-256 Encryption</h4>
                <p>Military-grade security for all backups</p>
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                st.markdown("""
                <div class='feature-box'>
                <h4>🧪 Sandbox Testing</h4>
                <p>Test skills safely before installing</p>
                </div>
                """, unsafe_allow_html=True)
            with cols[2]:
                st.markdown("""
                <div class='feature-box'>
                <h4>🦞 Moltbook Integration</h4>
                <p>Autonomous social posting</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Login box
            with st.form("login"):
                st.subheader("Dashboard Access")
                password = st.text_input("Password", type="password", 
                                        help="Demo: 'clawbackup-demo' or your own")
                
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("🔓 Login", use_container_width=True)
                with col2:
                    demo_btn = st.form_submit_button("👁️ View Demo", use_container_width=True)
                
                if submit:
                    if password == "clawbackup-demo":
                        st.session_state.authenticated = True
                        st.session_state.demo_mode = True
                        st.rerun()
                    else:
                        st.error("Invalid password. Try 'clawbackup-demo'")
                
                if demo_btn:
                    st.session_state.authenticated = True
                    st.session_state.demo_mode = True
                    st.rerun()
        
        st.markdown("---")
        st.caption("Built for SURGE × OpenClaw Hackathon | v1.0.0")
    st.stop()

# Main Dashboard (authenticated)
# Demo mode banner
if st.session_state.get('demo_mode', True):
    st.markdown("""
    <div class='demo-banner'>
    🎮 <b>DEMO MODE</b> — You're viewing sample data. 
    <a href="https://github.com/gertron88/clawbackup" target="_blank">Install locally</a> for real backups.
    </div>
    """, unsafe_allow_html=True)

# Header with connection status
header_col1, header_col2, header_col3, header_col4 = st.columns([2, 1, 1, 1])

with header_col1:
    st.markdown("<h1 class='main-header'>🛡️ ClawBackup</h1>", unsafe_allow_html=True)

with header_col2:
    if st.session_state.get('demo_mode'):
        st.info("⚪ Demo Mode", icon="ℹ️")
    else:
        st.success("🟢 Agent Connected", icon="✅")

with header_col3:
    moltbook_key = os.environ.get('MOLTBOOK_API_KEY')
    if moltbook_key:
        st.success("🦞 Moltbook Active", icon="✅")
    else:
        st.warning("🦞 Moltbook Off", icon="⚠️")

with header_col4:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Agent Configuration")
    
    agent_name = st.text_input("Agent Name", value="my-agent")
    
    st.markdown("---")
    
    # Quick stats in sidebar
    st.subheader("Quick Stats")
    st.metric("Total Backups", "5" if st.session_state.get('demo_mode') else "0")
    st.metric("Storage Used", "45.2 MB" if st.session_state.get('demo_mode') else "0 MB")
    st.metric("Last Backup", "2h ago" if st.session_state.get('demo_mode') else "Never")
    
    st.markdown("---")
    
    # Actions
    st.subheader("Quick Actions")
    
    if st.button("🔄 Create Backup", use_container_width=True, type="primary"):
        with st.spinner("Creating backup..."):
            time.sleep(1.5)
            if st.session_state.get('demo_mode'):
                st.success("✅ Demo backup created!")
                st.balloons()
            else:
                st.info("Install locally to create real backups")
    
    if st.button("🧪 Test Skill", use_container_width=True):
        st.session_state.active_tab = "Sandbox"
        st.rerun()
    
    st.markdown("---")
    
    # Links
    st.caption("Resources")
    st.markdown("[📁 GitHub Repo](https://github.com/gertron88/clawbackup)")
    st.markdown("[🦞 Moltbook](https://www.moltbook.com/u/altron)")
    st.markdown("[🏆 Hackathon](https://lablab.ai/event/surge-openclaw-hackathon)")

# Main content tabs
tab_labels = ["📊 Overview", "📦 Backups", "🧪 Sandbox", "🔐 Security", "⚙️ Settings"]
tabs = st.tabs(tab_labels)

# Tab 1: Overview
with tabs[0]:
    st.header("Dashboard Overview")
    
    # Metrics row
    met1, met2, met3, met4 = st.columns(4)
    
    with met1:
        st.metric(
            label="Backups",
            value="5" if st.session_state.get('demo_mode') else "0",
            delta="+1 today" if st.session_state.get('demo_mode') else None
        )
    
    with met2:
        st.metric(
            label="Secrets Protected",
            value="23" if st.session_state.get('demo_mode') else "0",
            delta="✅ Encrypted" if st.session_state.get('demo_mode') else None
        )
    
    with met3:
        st.metric(
            label="Sandbox Tests",
            value="12" if st.session_state.get('demo_mode') else "0",
            delta="3 blocked" if st.session_state.get('demo_mode') else None
        )
    
    with met4:
        st.metric(
            label="Moltbook Posts",
            value="8" if st.session_state.get('demo_mode') else "0",
            delta="Auto-posting" if st.session_state.get('demo_mode') else None
        )
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Recent Activity")
        
        activities = [
            {"time": "2 hours ago", "action": "Created backup", "detail": "Pre-Deployment-v1.0", "status": "success"},
            {"time": "5 hours ago", "action": "Sandbox test", "detail": "skill-analyzer-v2", "status": "safe"},
            {"time": "1 day ago", "action": "Restored backup", "detail": "Stable-v1.0", "status": "success"},
            {"time": "2 days ago", "action": "Moltbook post", "detail": "Backup milestone shared", "status": "info"},
        ] if st.session_state.get('demo_mode') else []
        
        if activities:
            for act in activities:
                icon = "✅" if act["status"] == "success" else "🧪" if act["status"] == "safe" else "ℹ️"
                with st.container():
                    cols = st.columns([1, 2, 3])
                    cols[0].caption(act["time"])
                    cols[1].markdown(f"{icon} **{act['action']}**")
                    cols[2].caption(act["detail"])
                st.divider()
        else:
            st.info("No activity yet. Create your first backup!")
    
    with col2:
        st.subheader("System Health")
        
        # Health indicators
        st.markdown("**Backup Engine**")
        st.progress(100, text="Operational")
        
        st.markdown("**Encryption**")
        st.progress(100, text="AES-256 Active")
        
        st.markdown("**Sandbox**")
        st.progress(95, text="Ready")
        
        st.markdown("**Moltbook**")
        if moltbook_key:
            st.progress(100, text="Connected")
        else:
            st.progress(0, text="Not Configured")

# Tab 2: Backups
with tabs[1]:
    st.header("Backup Management")
    
    # Backup list
    backups = [
        {"id": "bak_001", "name": "Pre-Deployment-v1.0", "date": "2026-02-26 14:30", "size": "12.3 MB", "files": 45, "secrets": 8, "real": True},
        {"id": "bak_002", "name": "Stable-v1.0", "date": "2026-02-25 18:30", "size": "11.8 MB", "files": 42, "secrets": 7, "real": True},
        {"id": "bak_003", "name": "Morning-Backup", "date": "2026-02-25 08:00", "size": "10.9 MB", "files": 40, "secrets": 6, "real": True},
        {"id": "bak_004", "name": "Pre-Skill-Install", "date": "2026-02-24 22:15", "size": "10.5 MB", "files": 38, "secrets": 6, "real": True},
        {"id": "bak_005", "name": "Initial-Backup", "date": "2026-02-24 10:00", "size": "9.8 MB", "files": 35, "secrets": 5, "real": True},
    ] if st.session_state.get('demo_mode') else []
    
    if backups:
        for i, backup in enumerate(backups):
            with st.container():
                cols = st.columns([2, 2, 1, 1, 1, 2])
                
                with cols[0]:
                    st.markdown(f"**{backup['name']}**")
                    st.caption(f"ID: `{backup['id']}`")
                
                with cols[1]:
                    st.caption(backup['date'])
                
                with cols[2]:
                    st.caption(backup['size'])
                
                with cols[3]:
                    st.caption(f"{backup['files']} files")
                
                with cols[4]:
                    st.markdown(f"<span class='security-badge'>{backup['secrets']} secrets 🔒</span>", unsafe_allow_html=True)
                
                with cols[5]:
                    rcol1, rcol2 = st.columns(2)
                    with rcol1:
                        if st.button("Restore", key=f"restore_{i}", use_container_width=True):
                            st.success(f"Restored {backup['name']}!")
                    with rcol2:
                        if st.button("Delete", key=f"delete_{i}", use_container_width=True):
                            st.error("Deleted")
            
            if i < len(backups) - 1:
                st.divider()
    else:
        st.info("No backups found. Click 'Create Backup' to get started!")

# Tab 3: Sandbox
with tabs[2]:
    st.header("Sandbox Testing")
    st.markdown("Test new skills in an isolated environment before installing")
    
    test_col1, test_col2 = st.columns([1, 1])
    
    with test_col1:
        st.subheader("Upload Skill")
        uploaded_file = st.file_uploader("Drop skill file here", type=['zip', 'py', 'js'])
        skill_path = st.text_input("Or enter path", placeholder="/path/to/skill")
        
        st.markdown("**Test Options**")
        timeout = st.slider("Timeout", 10, 300, 60)
        st.checkbox("Monitor file system", value=True)
        st.checkbox("Monitor network", value=True)
        st.checkbox("Check for secrets leakage", value=True)
        st.checkbox("Static code analysis", value=True)
    
    with test_col2:
        st.subheader("Test Results")
        
        if st.button("🚀 Run Test", type="primary", use_container_width=True):
            with st.spinner("Initializing sandbox..."):
                time.sleep(1)
            
            with st.spinner("Running security scans..."):
                time.sleep(1.5)
            
            # Mock results
            st.success("✅ Test Complete")
            
            result_cols = st.columns(3)
            with result_cols[0]:
                st.metric("Status", "🟢 SAFE")
            with result_cols[1]:
                st.metric("Duration", "2.3s")
            with result_cols[2]:
                st.metric("Alerts", "0")
            
            st.markdown("**Security Scan Results:**")
            checks = [
                ("✅", "No suspicious file access"),
                ("✅", "No unauthorized network calls"),
                ("✅", "No hardcoded secrets"),
                ("✅", "No eval() or exec() usage"),
                ("✅", "Resource limits respected"),
            ]
            for icon, check in checks:
                st.markdown(f"{icon} {check}")
            
            st.info("🛡️ Safe to install - No suspicious behavior detected")

# Tab 4: Security
with tabs[3]:
    st.header("Security Overview")
    
    sec1, sec2, sec3 = st.columns(3)
    
    with sec1:
        st.markdown("""
        ### 🔐 Encryption
        - **Algorithm:** AES-256-GCM
        - **Key Derivation:** PBKDF2 (100k iterations)
        - **Salt:** Random 16 bytes
        - **Status:** ✅ Active
        """)
    
    with sec2:
        st.markdown("""
        ### 🔍 Secret Detection
        - **API Keys:** Regex + entropy analysis
        - **Passwords:** Pattern matching
        - **Private Keys:** Format detection
        - **Status:** ✅ Active
        """)
    
    with sec3:
        st.markdown("""
        ### 🛡️ Sandbox
        - **Isolation:** Process separation
        - **Monitoring:** File + network
        - **Timeouts:** Configurable
        - **Status:** ✅ Ready
        """)
    
    st.markdown("---")
    
    st.subheader("Secret Scanning Results")
    
    secrets_found = [
        {"type": "API Key", "pattern": "sk-***...***", "count": 5, "redacted": True},
        {"type": "Password", "pattern": "***[REDACTED]***", "count": 3, "redacted": True},
        {"type": "Private Key", "pattern": "***[REDACTED]***", "count": 1, "redacted": True},
    ] if st.session_state.get('demo_mode') else []
    
    if secrets_found:
        for secret in secrets_found:
            cols = st.columns([2, 3, 1, 1])
            cols[0].markdown(f"**{secret['type']}**")
            cols[1].code(secret['pattern'])
            cols[2].caption(f"Found: {secret['count']}")
            cols[3].success("Redacted ✅")
    else:
        st.info("No secrets detected in recent backups")

# Tab 5: Settings
with tabs[4]:
    st.header("Configuration")
    
    sett_col1, sett_col2 = st.columns(2)
    
    with sett_col1:
        st.subheader("Backup Settings")
        st.checkbox("Auto-backup before skill install", value=True)
        st.checkbox("Auto-backup daily", value=False)
        st.checkbox("Encrypt all backups", value=True)
        st.number_input("Keep last N backups", min_value=1, max_value=100, value=10)
        
        st.markdown("---")
        
        st.subheader("Encryption")
        backup_password = st.text_input("Backup Password", type="password")
        st.caption("All backups encrypted with AES-256-GCM")
    
    with sett_col2:
        st.subheader("Moltbook Integration")
        moltbook_enabled = st.checkbox("Enable Moltbook posting", value=True)
        st.checkbox("Post on backup creation", value=True)
        st.checkbox("Post on restore completion", value=True)
        st.checkbox("Post sandbox results", value=True)
        
        if moltbook_enabled:
            if moltbook_key:
                st.success("🦞 Connected to @altron")
            else:
                st.warning("Add MOLTBOOK_API_KEY environment variable")
        
        st.markdown("---")
        
        st.subheader("Notifications")
        st.checkbox("Discord webhooks", value=False)
        st.checkbox("Email alerts", value=False)
    
    st.markdown("---")
    
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        st.success("Settings saved successfully!")

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

with footer_col1:
    st.caption("v1.0.0")

with footer_col2:
    st.caption("Built for SURGE × OpenClaw Hackathon | Contributors: Altron + Gertron | 🛡️ Protect your agents")

with footer_col3:
    st.caption("🔗 github.com/gertron88/clawbackup")
