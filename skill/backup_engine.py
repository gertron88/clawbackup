#!/usr/bin/env python3
"""
ClawBackup - Core Backup Engine
Handles creation, encryption, and storage of agent backups.
"""

import os
import json
import shutil
import tarfile
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class SecretScanner:
    """Scans files for secrets that should not be backed up."""
    
    # Patterns that indicate secrets
    SECRET_PATTERNS = [
        (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[\w\-]{16,}["\']?', 'API_KEY'),
        (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?[\w\-]{16,}["\']?', 'SECRET_KEY'),
        (r'(?i)(auth[_-]?token|authtoken)\s*[=:]\s*["\']?[\w\-]{16,}["\']?', 'AUTH_TOKEN'),
        (r'(?i)(private[_-]?key|privatekey)\s*[=:]\s*["\']?[\w\-]{32,}["\']?', 'PRIVATE_KEY'),
        (r'(?i)(password)\s*[=:]\s*["\'][^"\']{8,}["\']', 'PASSWORD'),
        (r'sk-[a-zA-Z0-9]{48}', 'OPENAI_KEY'),
        (r'gh[pousr]_[A-Za-z0-9_]{36,}', 'GITHUB_TOKEN'),
        (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY'),
        (r'[0-9a-zA-Z/+]{40}', 'GENERIC_SECRET'),  # High entropy strings
    ]
    
    # Files to always exclude
    EXCLUDED_FILES = [
        '.env', '.env.local', '.env.production',
        'id_rsa', 'id_ed25519', '.ssh/',
        'credentials.json', 'secrets.json',
        '*.key', '*.pem', '*.p12',
    ]
    
    @classmethod
    def scan_file(cls, filepath: str) -> List[Dict]:
        """Scan a file for secrets. Returns list of findings."""
        import re
        findings = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, secret_type in cls.SECRET_PATTERNS:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            findings.append({
                                'file': filepath,
                                'line': line_num,
                                'type': secret_type,
                                'position': match.span(),
                                'hash': hashlib.sha256(match.group().encode()).hexdigest()[:16]
                            })
        except Exception as e:
            pass  # Binary files, etc.
            
        return findings
    
    @classmethod
    def should_exclude(cls, filepath: str) -> bool:
        """Check if file should be excluded from backup."""
        filename = os.path.basename(filepath)
        
        for pattern in cls.EXCLUDED_FILES:
            if pattern.startswith('*'):
                if filename.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('/'):
                if pattern[:-1] in filepath:
                    return True
            elif filename == pattern:
                return True
        
        return False


class BackupEngine:
    """Core backup and restore functionality."""
    
    def __init__(self, agent_name: str, backup_dir: str = None):
        self.agent_name = agent_name
        self.backup_dir = Path(backup_dir or os.path.expanduser('~/.openclaw/backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_dir / 'backups.json'
        self._load_metadata()
    
    def _load_metadata(self):
        """Load backup metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {'backups': [], 'last_backup': None}
    
    def _save_metadata(self):
        """Save backup metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def create_backup(self, 
                      source_dir: str,
                      name: str = None,
                      password: str = None,
                      include_secrets: bool = False) -> Dict:
        """
        Create a backup of the agent.
        
        Args:
            source_dir: Directory to backup
            name: Optional name for this backup
            password: Encryption password (required)
            include_secrets: If False, secrets are redacted (default)
        
        Returns:
            Backup metadata
        """
        if not password:
            raise ValueError("Password required for encryption")
        
        timestamp = datetime.now().isoformat()
        backup_id = f"bak_{self.agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_name = name or f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create temp directory for staging
        staging_dir = self.backup_dir / f".staging_{backup_id}"
        staging_dir.mkdir(exist_ok=True)
        
        try:
            secrets_found = 0
            files_backed = 0
            
            # Walk source directory
            for root, dirs, files in os.walk(source_dir):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'backups']]
                
                for file in files:
                    src_path = Path(root) / file
                    rel_path = src_path.relative_to(source_dir)
                    dst_path = staging_dir / rel_path
                    
                    # Check if should exclude
                    if SecretScanner.should_exclude(str(src_path)):
                        continue
                    
                    # Ensure parent directory exists
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Scan for secrets
                    findings = SecretScanner.scan_file(str(src_path))
                    
                    if findings and not include_secrets:
                        # Redact secrets
                        with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        for finding in findings:
                            # Replace with placeholder
                            placeholder = f"[REDACTED_{finding['type']}:{finding['hash'][:8]}]"
                            # Simple string replacement (in production, use proper redaction)
                            content = content.replace(finding.get('match', ''), placeholder)
                        
                        with open(dst_path, 'w') as f:
                            f.write(content)
                        
                        secrets_found += len(findings)
                    else:
                        # Copy normally
                        shutil.copy2(src_path, dst_path)
                    
                    files_backed += 1
            
            # Create manifest
            manifest = {
                'backup_id': backup_id,
                'name': backup_name,
                'agent_name': self.agent_name,
                'timestamp': timestamp,
                'source_dir': str(source_dir),
                'files_backed': files_backed,
                'secrets_redacted': secrets_found,
                'version': '1.0.0'
            }
            
            with open(staging_dir / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create tarball
            tar_path = self.backup_dir / f"{backup_id}.tar.gz"
            with tarfile.open(tar_path, 'w:gz') as tar:
                tar.add(staging_dir, arcname='.')
            
            # Encrypt tarball
            salt = os.urandom(16)
            key = self._derive_key(password, salt)
            fernet = Fernet(key)
            
            with open(tar_path, 'rb') as f:
                encrypted_data = fernet.encrypt(f.read())
            
            enc_path = self.backup_dir / f"{backup_id}.enc"
            with open(enc_path, 'wb') as f:
                f.write(salt + encrypted_data)
            
            # Remove unencrypted tarball
            tar_path.unlink()
            
            # Calculate hash for integrity
            with open(enc_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Update metadata
            backup_info = {
                'id': backup_id,
                'name': backup_name,
                'timestamp': timestamp,
                'file': str(enc_path),
                'size': enc_path.stat().st_size,
                'hash': file_hash,
                'files_backed': files_backed,
                'secrets_redacted': secrets_found
            }
            
            self.metadata['backups'].append(backup_info)
            self.metadata['last_backup'] = timestamp
            self._save_metadata()
            
            # Cleanup staging
            shutil.rmtree(staging_dir)
            
            return backup_info
            
        except Exception as e:
            # Cleanup on failure
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            raise e
    
    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        return sorted(self.metadata['backups'], 
                     key=lambda x: x['timestamp'], 
                     reverse=True)
    
    def restore_backup(self, 
                       backup_id: str,
                       target_dir: str,
                       password: str) -> Dict:
        """
        Restore a backup.
        
        Args:
            backup_id: ID of backup to restore
            target_dir: Directory to restore to
            password: Encryption password
        
        Returns:
            Restore result
        """
        # Find backup
        backup = None
        for b in self.metadata['backups']:
            if b['id'] == backup_id:
                backup = b
                break
        
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")
        
        enc_path = Path(backup['file'])
        if not enc_path.exists():
            raise ValueError(f"Backup file not found: {enc_path}")
        
        # Verify integrity
        with open(enc_path, 'rb') as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        
        if current_hash != backup['hash']:
            raise ValueError("Backup integrity check failed! File may be corrupted.")
        
        # Decrypt
        with open(enc_path, 'rb') as f:
            data = f.read()
        
        salt = data[:16]
        encrypted = data[16:]
        
        key = self._derive_key(password, salt)
        fernet = Fernet(key)
        
        try:
            decrypted = fernet.decrypt(encrypted)
        except Exception:
            raise ValueError("Decryption failed. Wrong password?")
        
        # Extract to temp first
        temp_tar = self.backup_dir / f".restore_{backup_id}.tar.gz"
        with open(temp_tar, 'wb') as f:
            f.write(decrypted)
        
        # Extract
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(temp_tar, 'r:gz') as tar:
            tar.extractall(target_path)
        
        temp_tar.unlink()
        
        return {
            'success': True,
            'backup_id': backup_id,
            'restored_to': str(target_path),
            'timestamp': datetime.now().isoformat()
        }
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        for i, backup in enumerate(self.metadata['backups']):
            if backup['id'] == backup_id:
                enc_path = Path(backup['file'])
                if enc_path.exists():
                    enc_path.unlink()
                self.metadata['backups'].pop(i)
                self._save_metadata()
                return True
        return False


if __name__ == '__main__':
    # Test
    engine = BackupEngine('test-agent')
    print("ClawBackup engine initialized")
    print(f"Backup directory: {engine.backup_dir}")
