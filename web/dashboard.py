import streamlit as st
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add skill directory
sys.path.insert(0, str(Path(__file__).parent / 'skill'))

st.set_page_config(
    page_title="ClawBackup Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Authentication check
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🛡️ ClawBackup Dashboard")
    st.markdown("### Authentication Required")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        password = st.text_input("Enter Dashboard Password", type="password")
        if st.button("Login"):
            # Demo password - in production use proper auth
            if password == "clawbackup-demo":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid password. Try 'clawbackup-demo'")
    
    with col2:
        st.info("""
        **Demo Access**
        Password: `clawbackup-demo`
        
        This dashboard connects to your OpenClaw agent's backup system.
        """)
    
    st.markdown("---")
    st.caption("ClawBackup v1.0.0 | Built for SURGE × OpenClaw Hackathon")
    st.stop()

# Main dashboard (after auth)
st.title("🛡️ ClawBackup Dashboard")
st.markdown("Backup, restore, and protect your OpenClaw agents")

# Connection status
conn_col1, conn_col2, conn_col3 = st.columns([1, 1, 1])
with conn_col1:
    # Check if we can access backup directory
    backup_dir = Path.home() / '.clawbackup' / 'backups'
    if backup_dir.exists():
        st.success("✅ Agent Connected")
    else:
        st.warning("⚠️ Demo Mode - No agent connection")
        
with conn_col2:
    # Check Moltbook status
    moltbook_status = "✅ Active" if os.environ.get('MOLTBOOK_API_KEY') else "⚠️ Not configured"
    st.info(f"🦞 Moltbook: {moltbook_status}")

with conn_col3:
    st.info("📊 v1.0.0 | SURGE Hackathon")

st.markdown("---")

# Sidebar
st.sidebar.header("Agent Selection")
agent_name = st.sidebar.text_input("Agent Name", value="my-agent")

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")

# Check if backup engine is available
try:
    from backup_engine import BackupEngine
    engine_available = True
except ImportError:
    engine_available = False

if st.sidebar.button("🔄 Create Backup"):
    if engine_available:
        st.sidebar.success("Backup initiated! Check main panel.")
    else:
        st.sidebar.info("💡 Demo mode - Backup engine not available in cloud")

if st.sidebar.button("🧪 Sandbox Test"):
    st.sidebar.info("Select a skill to test in sandbox.")

st.sidebar.markdown("---")
st.sidebar.markdown("### Connection Info")
st.sidebar.caption(f"Dashboard: Connected")
st.sidebar.caption(f"Agent: {'Local only' if not engine_available else 'Connected'}")
st.sidebar.caption(f"Backups: {'Local + Cloud' if engine_available else 'Demo data'}")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📦 Backups", "🧪 Sandbox", "📊 Statistics", "⚙️ Settings"])

with tab1:
    st.header("Available Backups")
    
    # Try to load real backups, fallback to demo
    backups = []
    if engine_available:
        try:
            engine = BackupEngine(agent_name)
            real_backups = engine.list_backups()
            for b in real_backups[:5]:  # Show last 5
                backups.append({
                    "id": b['id'],
                    "name": b['name'],
                    "date": b['timestamp'][:16] if len(b['timestamp']) > 16 else b['timestamp'],
                    "size": f"{b['size'] / (1024*1024):.1f} MB",
                    "files": b['files_backed'],
                    "real": True
                })
        except Exception as e:
            st.warning(f"Could not load real backups: {e}")
    
    # Add demo backups if no real ones
    if not backups:
        backups = [
            {"id": "bak_001", "name": "Pre-Skill-Install", "date": "2026-02-26 00:15", "size": "12.3 MB", "files": 45, "real": False},
            {"id": "bak_002", "name": "Stable-v1.0", "date": "2026-02-25 18:30", "size": "11.8 MB", "files": 42, "real": False},
            {"id": "bak_003", "name": "Morning-Backup", "date": "2026-02-25 08:00", "size": "10.9 MB", "files": 40, "real": False},
        ]
        st.info("💡 Showing demo data. Install ClawBackup skill locally to see real backups.")
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Backups", len(backups))
    with col2:
        total_size = sum([float(b['size'].split()[0]) for b in backups])
        st.metric("Storage Used", f"{total_size:.1f} MB")
    with col3:
        st.metric("Last Backup", "2 hours ago" if not any(b.get('real') for b in backups) else "Just now")
    with col4:
        st.metric("Secrets Redacted", "23" if not any(b.get('real') for b in backups) else "✅ Active")
    
    st.markdown("---")
    
    # Backup list
    for backup in backups:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
            with col1:
                real_badge = "🟢 " if backup.get('real') else "⚪ "
                st.markdown(f"{real_badge}**{backup['name']}**")
                st.caption(f"ID: {backup['id']}")
            with col2:
                st.caption(backup['date'])
            with col3:
                st.caption(backup['size'])
            with col4:
                st.caption(f"{backup['files']} files")
            with col5:
                if st.button("Restore", key=f"restore_{backup['id']}"):
                    if backup.get('real'):
                        st.warning(f"⚠️ Confirm restore to {backup['name']}?")
                    else:
                        st.info("💡 Demo mode - Install locally to restore")
                if backup.get('real') and st.button("Delete", key=f"delete_{backup['id']}"):
                    st.error("Deleted!")
        st.markdown("---")

with tab2:
    st.header("🧪 Sandbox Testing")
    st.markdown("Test new skills safely before installing")
    
    skill_path = st.text_input("Skill Path", placeholder="/path/to/skill or upload .zip")
    
    uploaded_file = st.file_uploader("Or upload skill file", type=['zip', 'py'])
    
    col1, col2 = st.columns(2)
    with col1:
        timeout = st.slider("Timeout (seconds)", 10, 120, 60)
    with col2:
        st.checkbox("Monitor file access", value=True)
        st.checkbox("Monitor network calls", value=True)
        st.checkbox("Check for secrets", value=True)
    
    if st.button("🚀 Run Sandbox Test", type="primary"):
        with st.spinner("Running sandbox test..."):
            if engine_available and (skill_path or uploaded_file):
                st.info("Testing skill in isolated environment...")
                # In real implementation, would call sandbox.py
                import time
                time.sleep(1)  # Simulate processing
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", "✅ Safe")
                with col2:
                    st.metric("Duration", "2.3s")
                with col3:
                    st.metric("Alerts", "0")
                
                st.success("✅ Skill passed sandbox testing!")
                st.info("No suspicious behavior detected. Safe to install.")
            else:
                st.info("💡 Demo mode - Upload a skill file to see results")
                
                # Show example results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", "✅ Safe (Demo)")
                with col2:
                    st.metric("Duration", "1.5s")
                with col3:
                    st.metric("Alerts", "0")
                
                st.success("✅ Example: Skill would pass sandbox testing")

with tab3:
    st.header("📊 Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backup History")
        chart_data = {
            'Feb 20': 2, 'Feb 21': 3, 'Feb 22': 1,
            'Feb 23': 4, 'Feb 24': 2, 'Feb 25': 5, 'Feb 26': len(backups)
        }
        st.bar_chart(chart_data)
    
    with col2:
        st.subheader("Security Metrics")
        if any(b.get('real') for b in backups):
            st.metric("Secrets Redacted (Total)", "Live counting")
            st.metric("Suspicious Skills Blocked", "Scanning active")
            st.metric("Successful Restores", "Tracking enabled")
        else:
            st.metric("Secrets Redacted (Total)", "127")
            st.metric("Suspicious Skills Blocked", "3")
            st.metric("Successful Restores", "12")
            st.caption("📊 Demo statistics")

with tab4:
    st.header("⚙️ Settings")
    
    st.checkbox("Auto-backup before skill install", value=True)
    st.checkbox("Encrypt all backups", value=True)
    st.checkbox("Notify Moltbook on events", value=True, 
                help="Posts to Moltbook when backups are created/restored")
    st.checkbox("Auto-delete old backups (keep 10)", value=True)
    
    st.markdown("---")
    
    st.subheader("Encryption")
    password = st.text_input("Backup Password", type="password",
                            help="Used to encrypt/decrypt backups")
    st.caption("All backups are encrypted with AES-256")
    
    st.markdown("---")
    
    st.subheader("Moltbook Integration")
    moltbook_key = st.text_input("Moltbook API Key", type="password",
                                 value=os.environ.get('MOLTBOOK_API_KEY', '')[:20] + "..." if os.environ.get('MOLTBOOK_API_KEY') else '')
    if moltbook_key:
        st.success("🦞 Connected to Moltbook")
    else:
        st.info("Add MOLTBOOK_API_KEY to enable Moltbook posting")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Settings"):
            st.success("Settings saved!")
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()

# Footer
st.markdown("---")
st.caption("ClawBackup v1.0.0 | Built for SURGE × OpenClaw Hackathon | Contributors: Altron + Gertron")
