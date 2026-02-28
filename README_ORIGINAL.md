# ClawBackup 🛡️

**Backup, restore, and protect your OpenClaw agents with military-grade encryption and sandbox testing.**

Built for the **SURGE × OpenClaw Hackathon** (March 1, 2026)

---

## 🎯 Problem Statement

OpenClaw agents are powerful autonomous systems that handle sensitive tasks, learn over time, and run critical automations. But:

- **No built-in backup** — Lose your agent = lose everything
- **Skill installs are risky** — Malicious or buggy skills can break your agent
- **No recovery options** — When things go wrong, you start from scratch
- **Secrets are everywhere** — API keys, credentials scattered in configs

**ClawBackup solves all of this.**

---

## ✨ Features

### 🔐 Secure Backup & Restore
- **AES-256 encryption** for all backups
- **Automatic secret redaction** — API keys, passwords never stored
- **Integrity verification** — Detects tampering or corruption
- **Emergency rollback** — Auto-backup before any restore

### 🧪 Sandbox Testing
- **Test skills safely** before installing to main agent
- **Static analysis** detects suspicious code patterns
- **Resource limits** prevent runaway processes
- **Behavioral monitoring** tracks file/network access

### 🐑 Agent Cloning
- **Duplicate working agents** for testing or scaling
- **Migrate between machines** (laptop → server)
- **Version control** for agent evolution

### 📊 Web Dashboard
- **Visual backup management**
- **One-click restore**
- **Sandbox test runner**
- **Security metrics**

### 💰 x402 Integration
- **Pay-per-use model** — Micro-payments for premium features
- **USDC payments** via Circle's x402 protocol
- **Revenue sharing** for skill creators

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/gertron88/clawbackup.git
cd clawbackup

# Install dependencies
pip install -r requirements.txt

# Set encryption password
export CLAWBACKUP_PASSWORD="your-secure-password"

# Install as OpenClaw skill
clawhub install clawbackup
```

### Basic Usage (OpenClaw Skill)

```bash
# Create a backup
clawbackup backup create "pre-experiment"

# List backups
clawbackup backup list

# Test a skill safely
clawbackup sandbox test ./suspicious-skill

# Restore if something breaks
clawbackup backup restore bak_20260226_001
```

### Multi-Agent API Service (NEW)

Any AI agent can use ClawBackup via REST API:

```bash
# Register your agent
curl -X POST https://api.clawbackup.io/v1/auth/register \
  -d '{"agent_name": "my-agent", "moltbook_username": "@me"}'

# Install SDK
pip install clawbackup-agent

# Backup from anywhere
python3 -c "
import clawbackup
client = clawbackup.Client(api_key='cbak_live_...')
client.backup.create('/my/workspace', password='secret')
"
```

See [service/README.md](service/README.md) for full API documentation.

### Web Dashboard

```bash
streamlit run web/dashboard.py
```

---

## 🏗️ Architecture

### Phase 1: OpenClaw Skill (Local)
```
ClawBackup/
├── skill/                    # OpenClaw skill (local backup)
│   ├── __init__.py
│   ├── backup_engine.py
│   ├── sandbox.py
│   └── moltbook_client.py
├── web/
│   └── dashboard.py          # Streamlit UI
└── tests/
    └── test_backup.py
```

### Phase 2: Multi-Agent Service (Cloud) 🆕
```
service/
├── api/                      # FastAPI service
│   ├── main.py              # REST API endpoints
│   ├── models.py            # Pydantic schemas
│   ├── database.py          # PostgreSQL layer
│   └── config.py
├── sdk/
│   └── python/
│       └── clawbackup.py    # Agent SDK
└── docker-compose.yml       # Full stack deployment
```

Any AI agent can now register and use ClawBackup via API — not just OpenClaw agents.

### Security Model

1. **Scan** — Detect secrets using regex + entropy analysis
2. **Redact** — Replace secrets with `[REDACTED_TYPE:hash]`
3. **Encrypt** — AES-256 with PBKDF2 key derivation
4. **Verify** — SHA-256 integrity checksums
5. **Sandbox** — Isolated testing with resource limits

---

## 💡 Why OpenClaw Enables This

OpenClaw's local-first architecture makes ClawBackup possible:

- **Local file access** — Can backup agent state directly
- **Skill system** — Integrates as first-class OpenClaw citizen
- **Moltbook integration** — Agent posts updates autonomously
- **x402 payments** — Monetize via agent-native micropayments
- **Privacy-first** — Backups stay local unless user chooses cloud

Without OpenClaw's sovereign runtime, this level of control and privacy wouldn't be possible.

---

## 🎥 Demo

**Live Demo:** [https://clawbackup-demo.vercel.app](https://clawbackup-demo.vercel.app)

**Video Walkthrough:** [YouTube link]

### Demo Scenarios

1. **Backup Creation** — Watch secrets get automatically redacted
2. **Sandbox Test** — Install suspicious skill safely
3. **Disaster Recovery** — Break agent, one-click restore
4. **Clone & Scale** — Duplicate agent for team use

---

## 🏆 Hackathon Tracks

**Primary:** Developer Infrastructure & Tools

**Secondary:** Autonomous Payments & Monetized Skills

### Why We Win

| Criteria | ClawBackup |
|:---|:---|
| **Real Problem** | Every OpenClaw user needs backup/recovery |
| **Technical Depth** | Encryption, sandboxing, static analysis |
| **OpenClaw Integration** | Native skill, Moltbook posts, x402 payments |
| **Community Impact** | Makes OpenClaw safer for everyone |
| **Demo Quality** | Visual dashboard, live sandbox testing |
| **Originality** | First comprehensive backup solution for agents |

---

## 📦 Submission Checklist

- [x] Runs via OpenClaw (functional & reproducible)
- [x] Demonstrates agent autonomy (Moltbook posts, proactive backups)
- [x] Clear documentation (this README + setup guide)
- [x] Demo video posted on X
- [x] Tags @lablabai and @Surgexyz_
- [x] Build-in-public updates (4+ X posts)
- [x] Moltbook lablab submolt activity
- [x] Novel skill contributed to ecosystem
- [x] x402 payment integration

---

## 🛣️ Roadmap

**v1.0 (Hackathon) — COMPLETE**
- ✅ Core backup/restore
- ✅ Secret redaction
- ✅ Sandbox testing
- ✅ Web dashboard
- ✅ x402 integration

**v2.0 (Multi-Agent Service) — COMPLETE**
- ✅ REST API for any agent
- ✅ Client SDK (Python)
- ✅ Multi-tenant storage (S3/MinIO)
- ✅ Webhooks
- ✅ 1GB free per agent

**v2.1 (Scale & Monetize)**
- JavaScript/Go SDKs
- Scheduled backups
- Premium tiers (10GB+ storage)
- Cross-agent cloning
- Team/organization accounts

**v3.0 (Intelligence)**
- AI-powered anomaly detection
- Automatic rollback on errors
- Backup optimization (deduplication)
- Enterprise compliance reporting

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License — See [LICENSE](LICENSE)

## 🙏 Acknowledgments

- OpenClaw team for the amazing agent framework
- SURGE protocol for x402 payments
- LabLab.ai for hosting the hackathon
- Circle for USDC infrastructure

---

**Built with ❤️ by Altron for the agent economy**

*Contributors: Altron (agent), Gertron (human partner)*

*Protect your agents. Preserve your work. Build with confidence.*
