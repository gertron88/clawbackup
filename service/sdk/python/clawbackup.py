"""
ClawBackup Agent SDK
Easy backup/restore for AI agents

Usage:
    import clawbackup
    
    # Initialize
    client = clawbackup.Client(api_key="cbak_live_...")
    
    # Create backup
    backup = client.backup.create("/path/to/agent/workspace")
    
    # Restore elsewhere
    client.backup.restore(backup.id, "/new/location")
"""

import os
import json
import tarfile
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Union
from dataclasses import dataclass
from datetime import datetime
import requests


@dataclass
class BackupInfo:
    """Information about a backup."""
    id: str
    name: str
    size_bytes: int
    content_hash: str
    created_at: datetime
    expires_at: datetime
    tags: List[str]


class ClawBackupError(Exception):
    """Base exception for ClawBackup errors."""
    pass


class AuthenticationError(ClawBackupError):
    """API key invalid or expired."""
    pass


class QuotaExceededError(ClawBackupError):
    """Storage quota exceeded."""
    pass


class EncryptionHelper:
    """Client-side encryption helpers."""
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def encrypt_data(data: bytes, password: str) -> tuple[bytes, bytes]:
        """
        Encrypt data with password.
        Returns (encrypted_data, salt).
        """
        from cryptography.fernet import Fernet
        
        salt = os.urandom(16)
        key = EncryptionHelper.derive_key(password, salt)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)
        return encrypted, salt
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, password: str, salt: bytes) -> bytes:
        """Decrypt data with password and salt."""
        from cryptography.fernet import Fernet
        
        key = EncryptionHelper.derive_key(password, salt)
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_data)


class BackupManager:
    """Manage backups for an agent."""
    
    def __init__(self, client: 'Client'):
        self.client = client
    
    def create(
        self,
        source_path: Union[str, Path],
        name: Optional[str] = None,
        password: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> BackupInfo:
        """
        Create a backup of the agent workspace.
        
        Args:
            source_path: Path to agent workspace
            name: Optional name for backup
            password: Encryption password (defaults to BACKUP_PASSWORD env var)
            include_patterns: Glob patterns to include (default: all)
            exclude_patterns: Glob patterns to exclude
            tags: Tags for organization
        
        Returns:
            BackupInfo with backup details
        """
        source_path = Path(source_path).expanduser().resolve()
        
        if not source_path.exists():
            raise ClawBackupError(f"Source path does not exist: {source_path}")
        
        # Get password
        password = password or os.environ.get('BACKUP_PASSWORD')
        if not password:
            raise ClawBackupError(
                "Encryption password required. "
                "Pass as argument or set BACKUP_PASSWORD environment variable."
            )
        
        # Create tarball
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
            tar_path = tmp.name
        
        try:
            with tarfile.open(tar_path, 'w:gz') as tar:
                # Walk directory
                for file_path in source_path.rglob('*'):
                    if not file_path.is_file():
                        continue
                    
                    # Check excludes
                    rel_path = file_path.relative_to(source_path)
                    if exclude_patterns and self._matches_patterns(rel_path, exclude_patterns):
                        continue
                    
                    # Check includes (if specified, must match at least one)
                    if include_patterns and not self._matches_patterns(rel_path, include_patterns):
                        continue
                    
                    tar.add(file_path, arcname=rel_path)
            
            # Read and encrypt
            with open(tar_path, 'rb') as f:
                data = f.read()
            
            encrypted, salt = EncryptionHelper.encrypt_data(data, password)
            
            # Prepend salt to encrypted data
            encrypted_with_salt = salt + encrypted
            
            # Calculate hash for verification
            content_hash = hashlib.sha256(encrypted_with_salt).hexdigest()
            password_hash = hashlib.sha256(password.encode()).hexdigest()[:16]
            
            # Upload
            files = {'file': ('backup.tar.gz.enc', encrypted_with_salt, 'application/octet-stream')}
            data = {
                'name': name or f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'tags': json.dumps(tags or []),
                'encryption_hash': password_hash
            }
            
            response = self.client._request('POST', '/v1/backups', files=files, data=data)
            
            return BackupInfo(
                id=response['backup_id'],
                name=data['name'],
                size_bytes=response['size_bytes'],
                content_hash=response['content_hash'],
                created_at=datetime.utcnow(),
                expires_at=datetime.fromisoformat(response['expires_at'].replace('Z', '+00:00')),
                tags=tags or []
            )
        
        finally:
            # Cleanup
            if os.path.exists(tar_path):
                os.unlink(tar_path)
    
    def restore(
        self,
        backup_id: str,
        target_path: Union[str, Path],
        password: Optional[str] = None
    ) -> None:
        """
        Restore a backup to target path.
        
        Args:
            backup_id: Backup ID to restore
            target_path: Where to restore
            password: Encryption password (defaults to BACKUP_PASSWORD env var)
        """
        target_path = Path(target_path).expanduser().resolve()
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Get password
        password = password or os.environ.get('BACKUP_PASSWORD')
        if not password:
            raise ClawBackupError("Encryption password required")
        
        # Download backup
        response = self.client._request('GET', f'/v1/backups/{backup_id}/download', stream=True)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as tmp:
            encrypted_path = tmp.name
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
        
        try:
            # Read and decrypt
            with open(encrypted_path, 'rb') as f:
                encrypted_with_salt = f.read()
            
            salt = encrypted_with_salt[:16]
            encrypted = encrypted_with_salt[16:]
            
            decrypted = EncryptionHelper.decrypt_data(encrypted, password, salt)
            
            # Extract tarball
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
                tar_path = tmp.name
                tmp.write(decrypted)
            
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(target_path)
            
            os.unlink(tar_path)
        
        finally:
            os.unlink(encrypted_path)
    
    def list(self, limit: int = 20, offset: int = 0, tag: Optional[str] = None) -> List[BackupInfo]:
        """List backups."""
        params = {'limit': limit, 'offset': offset}
        if tag:
            params['tag'] = tag
        
        response = self.client._request('GET', '/v1/backups', params=params)
        
        return [
            BackupInfo(
                id=b['backup_id'],
                name=b['name'],
                size_bytes=b['size_bytes'],
                content_hash=b['content_hash'],
                created_at=datetime.fromisoformat(b['created_at'].replace('Z', '+00:00')),
                expires_at=datetime.fromisoformat(b['expires_at'].replace('Z', '+00:00')),
                tags=b.get('tags', [])
            )
            for b in response['backups']
        ]
    
    def delete(self, backup_id: str) -> None:
        """Delete a backup."""
        self.client._request('DELETE', f'/v1/backups/{backup_id}')
    
    def _matches_patterns(self, path: Path, patterns: List[str]) -> bool:
        """Check if path matches any of the glob patterns."""
        import fnmatch
        path_str = str(path)
        for pattern in patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_str, f"*/{pattern}"):
                return True
        return False


class Client:
    """ClawBackup API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000"
    ):
        """
        Initialize ClawBackup client.
        
        Args:
            api_key: API key (or from CLAWBACKUP_API_KEY env var)
            base_url: API base URL
        """
        self.api_key = api_key or os.environ.get('CLAWBACKUP_API_KEY')
        if not self.api_key:
            raise ClawBackupError(
                "API key required. Pass as argument or set CLAWBACKUP_API_KEY environment variable."
            )
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}'
        })
        
        # Sub-managers
        self.backup = BackupManager(self)
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Union[Dict, requests.Response]:
        """Make API request."""
        url = f"{self.base_url}{endpoint}"
        
        # Separate stream param
        stream = kwargs.pop('stream', False)
        
        response = self.session.request(method, url, stream=stream, **kwargs)
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 403:
            raise QuotaExceededError("Storage quota exceeded")
        elif response.status_code == 404:
            raise ClawBackupError("Backup not found")
        elif not response.ok:
            try:
                error = response.json().get('detail', response.text)
            except:
                error = response.text
            raise ClawBackupError(f"API error: {error}")
        
        if stream:
            return response
        
        return response.json()
    
    def ping(self) -> bool:
        """Check if service is reachable."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.ok
        except:
            return False
    
    def get_info(self) -> Dict:
        """Get service info and limits."""
        return self._request('GET', '/v1/info')
    
    def get_me(self) -> Dict:
        """Get current agent info."""
        return self._request('GET', '/v1/auth/me')


# Convenience function
def snap(
    path: Union[str, Path],
    name: Optional[str] = None,
    password: Optional[str] = None
) -> BackupInfo:
    """
    Quick backup with default client.
    
    Usage:
        import clawbackup
        clawbackup.snap("/path/to/workspace", name="pre-update")
    """
    client = Client()
    return client.backup.create(path, name=name, password=password)


def register(
    agent_name: str,
    moltbook_username: Optional[str] = None,
    base_url: str = "http://localhost:8000"
) -> str:
    """
    Register a new agent and get API key.
    
    Returns the API key (save this - shown only once).
    """
    response = requests.post(
        f"{base_url}/v1/auth/register",
        json={
            'agent_name': agent_name,
            'moltbook_username': moltbook_username
        }
    )
    
    if not response.ok:
        raise ClawBackupError(f"Registration failed: {response.text}")
    
    data = response.json()
    return data['api_key']


__all__ = [
    'Client',
    'BackupInfo',
    'ClawBackupError',
    'AuthenticationError',
    'QuotaExceededError',
    'snap',
    'register'
]
