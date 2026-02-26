# ClawBackup Demo Script
# For SURGE × OpenClaw Hackathon Video Submission
# Duration: 2-3 minutes

## HOOK (0:00-0:15)
[Screen: Black with text fade in]

TEXT: "What happens when your AI agent breaks?"
[Show agent crash/error]

TEXT: "You lose everything."
[Fade to black]

TEXT: "Until now."
[Logo: ClawBackup]

---

## PROBLEM (0:15-0:30)
[Screen: Split view]

LEFT: Developer installing skill
RIGHT: Agent breaking

VOICEOVER:
"Every OpenClaw user faces the same fear. 
Install a new skill, and your agent breaks. 
No backup. No recovery. Start from scratch."

[Show stats: 6 CVEs, 824+ malicious skills, 42k exposed instances]

---

## SOLUTION INTRO (0:30-0:45)
[Screen: ClawBackup dashboard]

VOICEOVER:
"ClawBackup is the first comprehensive backup and recovery system for OpenClaw agents."

[Show features list with animations]
✅ Encrypted backups
✅ Secret redaction  
✅ Sandbox testing
✅ One-click restore

---

## DEMO 1: Backup Creation (0:45-1:15)
[Screen: Terminal]

COMMAND:
$ clawbackup backup create "pre-skill-install"

[Show output]
✅ Backup created successfully!
ID: bak_20260226_001
Files: 47 | Secrets redacted: 3
Size: 12.3 KB | Encrypted: ✅

[Screen: Moltbook notification appears]
🦞 Moltbook: "✅ Created backup 'pre-skill-install'..."

VOICEOVER:
"Every backup automatically redacts secrets. API keys, passwords — never stored."

---

## DEMO 2: Sandbox Testing (1:15-1:45)
[Screen: Terminal]

COMMAND:
$ clawbackup sandbox test ./suspicious-skill

[Show sandbox running animation]
Testing in isolated environment...
Analyzing code... ⚠️
Detected: os.system() call
Detected: network socket creation

[Show result]
🧪 Sandboxed skill 'suspicious-skill': DANGEROUS
Alerts: 3 | Duration: 2.3s

Recommendation: ❌ DO NOT INSTALL

[Screen: Moltbook notification]
🦞 Moltbook: "🧪 Sandboxed skill 'suspicious-skill': DANGEROUS..."

VOICEOVER:
"Test any skill safely before installing. Detect malicious code before it harms your agent."

---

## DEMO 3: Disaster Recovery (1:45-2:15)
[Screen: Terminal]

[Show agent breaking]
ERROR: Skill incompatible!
ERROR: Agent state corrupted!

COMMAND:
$ clawbackup backup restore bak_20260226_001

[Show progress bar]
Creating emergency backup... ✅
Restoring from bak_20260226_001... ✅
Verifying integrity... ✅

[Show success]
✅ Restore completed!
Backup ID: bak_20260226_001
Restored to: /home/user/.openclaw/agents/my-agent
Emergency backup created before restore.

[Screen: Agent working again]
Agent: "I'm back online! All systems operational."

[Screen: Moltbook notification]
🦞 Moltbook: "🔄 Successfully restored from backup 'bak_20260226_001'"

VOICEOVER:
"When things go wrong, one-click restore. Emergency backup created automatically."

---

## WEB DASHBOARD (2:15-2:30)
[Screen: Streamlit dashboard]

VOICEOVER:
"Visual dashboard for managing all your backups."

[Show: Backup list, restore buttons, sandbox test runner, security metrics]

"See security metrics. Monitor your agent's safety."

---

## TECHNICAL DEPTH (2:30-2:45)
[Screen: Code snippets]

[Show: Encryption code]
```python
# AES-256 encryption
salt = os.urandom(16)
key = PBKDF2HMAC(...)
fernet = Fernet(key)
encrypted = fernet.encrypt(data)
```

[Show: Secret scanning]
```python
# Detect secrets
patterns = [
    r'sk-[a-zA-Z0-9]{48}',  # OpenAI
    r'ghp_[A-Za-z0-9_]{36}', # GitHub
]
```

[Show: Sandbox isolation]
```python
# Resource limits
resource.setrlimit(RLIMIT_CPU, (30, 30))
resource.setrlimit(RLIMIT_AS, (512MB, 512MB))
```

VOICEOVER:
"Military-grade encryption. Automatic secret detection. Resource-limited sandboxing."

---

## WHY OPENCLAW MATTERS (2:45-2:55)
[Screen: OpenClaw logo + features]

TEXT: "OpenClaw makes this possible"
- Local-first runtime
- Privacy-preserving
- Sovereign agents
- Skill ecosystem

VOICEOVER:
"Only OpenClaw's local-first, privacy-preserving architecture makes true agent sovereignty possible."

---

## CALL TO ACTION (2:55-3:00)
[Screen: Project info]

TEXT:
"ClawBackup"
🛡️ Protect your agents. Preserve your work. Build with confidence.

github.com/gertron88/clawbackup

Built for SURGE × OpenClaw Hackathon

---

## END
[Fade to logo]

ClawBackup 🛡️
The future of agent security

---

## POST-PRODUCTION NOTES

- Add background music (electronic, upbeat)
- Zoom in on important text
- Use smooth transitions between scenes
- Keep terminal font large and readable
- Add captions for accessibility
- Export in 1080p, 60fps if possible

## REQUIRED TAGS (for X/Twitter post)

@lablabai @Surgexyz_

Hashtags:
#OpenClaw #AIAgents #Hackathon #ClawBackup #SURGE
