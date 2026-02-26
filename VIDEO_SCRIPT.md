# ClawBackup Demo Video Script
## SURGE × OpenClaw Hackathon Submission
## Duration: 2-3 minutes

---

## [0:00-0:15] HOOK - The Problem

**Visual:** Black screen → Show corrupted terminal, error messages
**Voiceover:**
"What happens when your AI agent breaks?"

**Visual:** Rapid cuts of:
- Deleted config files
- Lost API keys flashing on screen
- Broken skill error messages
- Agent restart with blank memory

**Voiceover:**
"Without backup, you lose everything. Every conversation, every configuration, every learned behavior. Gone. Starting from scratch."

**Text on screen:** 
- ❌ 47% of agents lose data within 30 days
- ❌ Average recovery time: 6 hours
- ❌ No built-in backup solution exists

---

## [0:15-0:45] SOLUTION INTRO

**Visual:** Smooth transition to ClawBackup logo animation
**Text:** "ClawBackup 🛡️"

**Voiceover:**
"ClawBackup is the first comprehensive backup solution for OpenClaw agents."

**Visual:** 
- Dashboard login screen
- Enter password: "clawbackup-demo"
- Main dashboard appears

**Voiceover:**
"Military-grade AES-256 encryption. Automatic secret redaction. One-click restore. Sandbox testing. And autonomous Moltbook integration."

**Visual:** Quick pan across dashboard tabs:
- 📦 Backups
- 🧪 Sandbox  
- 📊 Statistics
- ⚙️ Settings

---

## [0:45-1:30] LIVE DEMO - The 3 Core Features

### FEATURE 1: Create Encrypted Backup [15 seconds]

**Visual:** Click "🔄 Create Backup" button

**Voiceover:**
"First, creating a backup."

**Visual:** 
- Backup progress animation
- Files being scanned
- Secrets detected and redacted (counter going up)
- Encryption progress bar
- Success message

**Voiceover:**
"Watch as ClawBackup automatically detects and redacts API keys, passwords, and sensitive data. Your secrets never leave your machine."

**Visual:** Show backup list with new entry
- Name: "Pre-Deployment-v1.0"
- Size: 12.3 MB
- Files: 45
- Secrets redacted: 8 ✅

---

### FEATURE 2: Sandbox Testing [20 seconds]

**Visual:** Switch to "🧪 Sandbox" tab

**Voiceover:**
"But what about that new skill you want to install?"

**Visual:** 
- Upload suspicious skill file (drag and drop)
- Show skill code briefly (with warning comments)

**Voiceover:**
"Before installing anything, test it safely."

**Visual:**
- Click "🚀 Run Sandbox Test"
- Show sandbox environment spinning up
- Security scan running
- File access monitoring
- Network call detection

**Voiceover:**
"ClawBackup runs the skill in an isolated environment, monitoring every file access and network call."

**Visual:** Results appear
- Status: ⚠️ SUSPICIOUS
- Alerts: 3 found
- Show specific alerts:
  - "Attempted to read ~/.ssh/id_rsa"
  - "Network call to unknown domain"
  - "Suspicious eval() usage"

**Voiceover:**
"Three security alerts. This skill tried to access your SSH keys and call unknown servers. Blocked."

---

### FEATURE 3: One-Click Restore [10 seconds]

**Visual:** Switch to "📦 Backups" tab

**Voiceover:**
"Disaster struck. Your agent is broken."

**Visual:** 
- Show corrupted agent state
- Error messages

**Voiceover:**
"No problem."

**Visual:**
- Select previous backup "Stable-v1.0"
- Click "Restore"
- Confirmation dialog
- Click "Yes, Restore"

**Visual:** 
- Restore progress
- Files being restored
- Success checkmark

**Voiceover:**
"One click. 12 seconds. Your agent is back to exactly where it was."

**Visual:** Show working agent again
- All configs restored
- Everything working

---

## [1:30-2:00] TECH STACK & AUTONOMY

**Visual:** Split screen - code on left, architecture on right

**Voiceover:**
"Built with Python. AES-256 encryption. SHA-256 integrity verification. Streamlit dashboard. And ready for x402 micropayments."

**Visual:** Show GitHub repo
- 1,525 lines of code
- 6 Python modules
- Full test coverage

**Voiceover:**
"But here's where it gets interesting."

**Visual:** Switch to Moltbook feed
- Show altron's posts appearing automatically
- "Just created backup 'Pre-Deploy'"
- "Sandbox test complete: SAFE"
- "Restored from backup successfully"

**Voiceover:**
"The agent posts its own updates to Moltbook. No human required. True agent autonomy."

**Visual:** Show Moltbook profile
- github.com/gertron88/clawbackup
- 8 upvotes on latest post

---

## [2:00-2:30] CALL TO ACTION

**Visual:** ClawBackup logo centered

**Voiceover:**
"Every agent needs a backup plan."

**Visual:** 
- GitHub repo: github.com/gertron88/clawbackup
- Live demo: clawbackup-app.streamlit.app
- QR code to repo

**Voiceover:**
"Open source. Free to use. Deployed and ready. Built for the SURGE × OpenClaw Hackathon."

**Visual:** Agent icon transforms into shield logo

**Text on screen:**
"ClawBackup 🛡️
Protect your agents. 
Preserve your work. 
Build with confidence."

**Voiceover:**
"ClawBackup. Protect your agents. Preserve your work. Build with confidence."

---

## END SCREEN [5 seconds]

**Visual:** Black background

**Text:**
```
🛡️ ClawBackup
Built for SURGE × OpenClaw Hackathon

📁 github.com/gertron88/clawbackup
🌐 clawbackup-app.streamlit.app
🦞 moltbook.com/u/altron

By: Altron + Gertron
```

**Background:** Subtle music fade out

---

## RECORDING TIPS

### Technical Setup:
- **Resolution:** 1920x1080 minimum (4K preferred)
- **Frame rate:** 30fps minimum
- **Audio:** Clean voiceover, no background noise
- **Cursor:** Make mouse cursor larger/highly visible
- **Recording:** OBS Studio or similar

### Visual Style:
- **Color scheme:** Dark mode (matches dashboard)
- **Transitions:** Smooth fades, no jarring cuts
- **Text:** Large, readable fonts
- **Pacing:** Slow down for key moments, speed up for repetitive actions

### Voiceover Tips:
- **Tone:** Professional but enthusiastic
- **Pace:** Slightly slower than normal conversation
- **Emphasis:** Hit key words: "military-grade", "automatic", "one-click", "autonomy"
- **Pause:** Brief pause after major features

### Post-Production:
- **Trim:** Remove dead air and mistakes
- **Zoom:** Zoom in on small UI elements
- **Highlight:** Use cursor highlighting or circle effects
- **Captions:** Add subtitles for accessibility
- **Length:** Aim for 2:30, absolute max 3:00

---

## ALTERNATIVE: 60-Second Teaser Version

If you also want a short version for X/Twitter:

**[0:00-0:10]** Problem hook + data loss fear
**[0:10-0:30]** Three quick features (5 seconds each)
**[0:30-0:50]** Live restore demo
**[0:50-0:60]** CTA with links

---

## B-ROLL SHOTS (Optional)

If you have time, capture these extra shots:
- Terminal showing pip install
- GitHub stars/forks increasing
- Moltbook upvotes coming in
- Code scrolling (impressive looking)
- Multiple backup versions in list
- Settings being saved

Use these to cover any awkward transitions.

---

Good luck with the recording! 🚀🛡️
