# ClawBackup Architecture & Security Design

## Overview
ClawBackup is an OpenClaw skill that provides backup, restore, cloning, and sandbox capabilities for agents.

---

## How the Agent Utilizes It

### 1. Automatic Backup Triggers
```
Agent can configure:
- Time-based: "Backup every 6 hours"
- Event-based: "Backup before installing any skill"
- Manual: "ClawBackup, create snapshot now"
```

### 2. Agent Commands
```
"backup create [name]"           → Create named snapshot
"backup restore [id]"            → Restore to snapshot
"backup clone [new-agent-name]"  → Duplicate this agent
"backup sandbox [skill-name]"    → Test skill safely
"backup list"                    → Show all snapshots
"backup schedule [frequency]"    → Auto-backup settings
```

### 3. Proactive Protection
- Auto-backup before risky operations
- Alert agent when backup is stale
- Offer to restore if agent detects issues

---

## Security Architecture

### 🔐 CRITICAL: Secrets Handling

**NEVER backed up:**
```yaml
excluded_from_backup:
  - .env files
  - *_KEY, *_SECRET, *_TOKEN environment variables
  - .openclaw/credentials/
  - AWS credentials
  - API keys in config files
  - Private keys (ssh, wallet)
  - Session tokens
```

**Backed up (safe):**
```yaml
included_in_backup:
  - Agent configuration (skills list, settings)
  - Memory/conversation history
  - Custom prompts/personality
  - Installed skills manifest (not the secrets they use)
  - Workflow definitions
  - State files
```

### Encryption Layers

```
1. At-rest encryption: AES-256 for backup files
2. In-transit: TLS 1.3 for cloud uploads
3. Key derivation: Argon2id for password-based keys
4. Optional: Hardware security module (HSM) integration
```

### Access Control

```yaml
permissions:
  backup_create: "anyone"           # Agent can backup itself
  backup_restore: "agent + owner"   # Requires human confirmation for restore
  backup_clone: "owner_only"        # Only human can clone (creates new agent)
  backup_delete: "owner_only"       # Only human can delete backups
  sandbox_mode: "agent"             # Agent can sandbox freely
```

---

## Data Flow

### Creating a Backup
```
1. Agent requests backup
2. ClawBackup pauses agent activity (optional)
3. Scan for secrets (regex patterns, entropy analysis)
4. Redact any found secrets → replace with [REDACTED_SECRET:hash]
5. Compress + encrypt state
6. Generate integrity hash (SHA-256)
7. Store locally (default) or upload to cloud
8. Resume agent activity
9. Post confirmation to Moltbook
```

### Restoring a Backup
```
1. Owner requests restore (2FA recommended)
2. ClawBackup verifies backup integrity
3. Create emergency backup of current state (in case restore fails)
4. Stop current agent
5. Restore files from backup
6. Prompt for missing secrets (they weren't backed up!)
7. Verify agent starts correctly
8. If fails → auto-rollback to pre-restore state
```

### Sandbox Mode
```
1. Create isolated container/directory
2. Clone agent state into sandbox
3. Install skill in sandbox only
4. Monitor for:
   - File system access outside allowed paths
   - Network calls to suspicious domains
   - Attempts to access secrets
   - Resource exhaustion (CPU/memory)
5. Report findings to agent
6. Destroy sandbox after test
```

---

## Storage Options

### Local (Default - Free)
```yaml
path: ~/.openclaw/backups/
retention: 10 most recent backups
encryption: yes (password-protected)
```

### Cloud (x402 Payments)
```yaml
provider: IPFS / Arweave / S3
encryption: yes (client-side)
payment: x402 micropayments per GB/month
retention: configurable
redundancy: 3+ copies
```

### Hybrid (Recommended)
```yaml
recent_backups: local (fast restore)
archive_backups: cloud (disaster recovery)
auto_tier: Move old backups to cloud after 7 days
```

---

## Moltbook Integration

### What the Agent Posts

**On backup create:**
```
✅ Created backup "pre-skill-install"
Size: 2.3MB | Secrets redacted: 3 | Encrypted: ✅
Backup ID: bak_2026_02_26_001
```

**On restore:**
```
🔄 Restored to backup "stable-v1.2"
Restored in 12s | All systems operational
```

**On sandbox detection:**
```
⚠️ Sandboxed skill "unknown-skill" attempted:
- File access: /etc/passwd ❌ BLOCKED
- Network call: suspicious-domain.com ❌ BLOCKED
Recommendation: DO NOT INSTALL
```

---

## Implementation Structure

```
clawbackup/
├── skill/
│   ├── __init__.py
│   ├── backup_engine.py      # Core backup logic
│   ├── secret_scanner.py     # Detects secrets in files
│   ├── encryptor.py          # Encryption/decryption
│   ├── sandbox.py            # Isolated testing
│   └── moltbook_notifier.py  # Posts updates
├── web/
│   ├── dashboard.py          # Streamlit/Next.js UI
│   ├── restore_wizard.py     # Step-by-step restore
│   └── sandbox_viewer.py     # Watch sandbox activity
├── tests/
│   └── test_backup_restore.py
└── docs/
    └── SETUP.md
```

---

## Security Checklist

- [ ] Secrets never leave the machine unencrypted
- [ ] All backups encrypted with AES-256
- [ ] Integrity verification on every restore
- [ ] Auto-rollback if restore fails
- [ ] Sandbox network isolation
- [ ] Resource limits in sandbox (prevent DoS)
- [ ] Audit log of all backup/restore operations
- [ ] Optional: Hardware wallet for backup signing

---

## x402 Revenue Model

```yaml
free_tier:
  - 5 local backups
  - Basic encryption
  - Community support

premium_tier:  # $5/month in USDC via x402
  - Unlimited backups
  - Cloud storage (IPFS/Arweave)
  - Advanced sandboxing
  - Priority support
  - Team sharing (multiple agents)

enterprise_tier:  # Custom pricing
  - Self-hosted backup servers
  - SSO integration
  - Compliance reporting
  - Dedicated support
```

Ready to build this? 🚀
