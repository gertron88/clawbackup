import streamlit as st
import json
import sys
from pathlib import Path

# Add skill directory
sys.path.insert(0, str(Path(__file__).parent / 'skill'))

st.set_page_config(
    page_title="ClawBackup Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ ClawBackup Dashboard")
st.markdown("Backup, restore, and protect your OpenClaw agents")

# Sidebar
st.sidebar.header("Agent Selection")
agent_name = st.sidebar.text_input("Agent Name", value="my-agent")

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")
if st.sidebar.button("🔄 Create Backup"):
    st.sidebar.success("Backup initiated! Check main panel.")

if st.sidebar.button("🧪 Sandbox Test"):
    st.sidebar.info("Select a skill to test in sandbox.")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📦 Backups", "🧪 Sandbox", "📊 Statistics", "⚙️ Settings"])

with tab1:
    st.header("Available Backups")
    
    # Mock data for demo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Backups", "5")
    with col2:
        st.metric("Storage Used", "45.2 MB")
    with col3:
        st.metric("Last Backup", "2 hours ago")
    with col4:
        st.metric("Secrets Redacted", "23")
    
    st.markdown("---")
    
    # Backup list
    backups = [
        {"id": "bak_001", "name": "Pre-Skill-Install", "date": "2026-02-26 00:15", "size": "12.3 MB", "files": 45},
        {"id": "bak_002", "name": "Stable-v1.0", "date": "2026-02-25 18:30", "size": "11.8 MB", "files": 42},
        {"id": "bak_003", "name": "Morning-Backup", "date": "2026-02-25 08:00", "size": "10.9 MB", "files": 40},
    ]
    
    for backup in backups:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
            with col1:
                st.markdown(f"**{backup['name']}**")
                st.caption(f"ID: {backup['id']}")
            with col2:
                st.caption(backup['date'])
            with col3:
                st.caption(backup['size'])
            with col4:
                st.caption(f"{backup['files']} files")
            with col5:
                if st.button("Restore", key=f"restore_{backup['id']}"):
                    st.warning(f"⚠️ Confirm restore to {backup['name']}?")
                if st.button("Delete", key=f"delete_{backup['id']}"):
                    st.error("Deleted!")
        st.markdown("---")

with tab2:
    st.header("🧪 Sandbox Testing")
    st.markdown("Test new skills safely before installing")
    
    skill_path = st.text_input("Skill Path", placeholder="/path/to/skill")
    
    col1, col2 = st.columns(2)
    with col1:
        timeout = st.slider("Timeout (seconds)", 10, 120, 60)
    with col2:
        st.checkbox("Monitor file access", value=True)
        st.checkbox("Monitor network calls", value=True)
    
    if st.button("🚀 Run Sandbox Test", type="primary"):
        with st.spinner("Running sandbox test..."):
            st.info("Testing skill in isolated environment...")
            
            # Mock results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", "✅ Safe")
            with col2:
                st.metric("Duration", "2.3s")
            with col3:
                st.metric("Alerts", "0")
            
            st.success("✅ Skill passed sandbox testing!")
            st.info("No suspicious behavior detected. Safe to install.")

with tab3:
    st.header("📊 Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backup History")
        st.bar_chart({
            'Feb 20': 2,
            'Feb 21': 3,
            'Feb 22': 1,
            'Feb 23': 4,
            'Feb 24': 2,
            'Feb 25': 5,
            'Feb 26': 1
        })
    
    with col2:
        st.subheader("Security Metrics")
        st.metric("Secrets Redacted (Total)", "127")
        st.metric("Suspicious Skills Blocked", "3")
        st.metric("Successful Restores", "12")

with tab4:
    st.header("⚙️ Settings")
    
    st.checkbox("Auto-backup before skill install", value=True)
    st.checkbox("Encrypt all backups", value=True)
    st.checkbox("Notify Moltbook on events", value=True)
    st.checkbox("Auto-delete old backups (keep 10)", value=True)
    
    st.markdown("---")
    
    st.subheader("Encryption")
    password = st.text_input("Backup Password", type="password")
    st.caption("All backups are encrypted with AES-256")
    
    st.markdown("---")
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved!")

# Footer
st.markdown("---")
st.caption("ClawBackup v1.0.0 | Built for SURGE × OpenClaw Hackathon")
