"""
MoltVault Agent SDK - Hosted Version
Works with Vercel + Supabase backend
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
    id: str
    name: str
    size_bytes: int
    content_hash: str
    created_at: datetime
    expires_at: datetime
    tags: List[str]


class MoltVaultError(Exception):
    pass


class AuthenticationError(MoltVaultError):
    pass


class QuotaExceededError(MoltVaultError):
    pass


class EncryptionHelper:
    """Client-side encryption - data never leaves agent unencrypted."""
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    @staticmethod
    def encrypt_data(data: bytes, password: str) -> tuple[bytes, bytes]:
        from cryptography.fernet import Fernet
        
        salt = os.urandom(16)
        key = EncryptionHelper.derive_key(password, salt)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)
        return encrypted, salt
    
    @staticmethod
    def decrypt_data(encrypted_data: bytes, password: str, salt: bytes) -> bytes:
        from cryptography.fernet import Fernet
        return Fernet(EncryptionHelper.derive_key(password, salt)).decrypt(encrypted_data)
    
    @staticmethod
    def encrypt_file(input_path: Union[str, Path], output_path: Union[str, Path], password: str):
        """Encrypt a file in-place style (creates new encrypted file)."""
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted, salt = EncryptionHelper.encrypt_data(data, password)
        
        with open(output_path, 'wb') as f:
            f.write(salt + encrypted)
    
    @staticmethod
    def decrypt_file(input_path: Union[str, Path], output_path: Union[str, Path], password: str):
        """Decrypt a file."""
        with open(input_path, 'rb') as f:
            data = f.read()
        
        salt = data[:16]
        encrypted = data[16:]
        
        decrypted = EncryptionHelper.decrypt_data(encrypted, password, salt)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)


class BackupManager:
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
        """Create and upload a backup."""
        source_path = Path(source_path).expanduser().resolve()
        
        if not source_path.exists():
            raise MoltVaultError(f"Source path does not exist: {source_path}")
        
        password = password or os.environ.get('BACKUP_PASSWORD')
        if not password:
            raise MoltVaultError("Encryption password required")
        
        # Create tarball
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
            tar_path = tmp.name
        
        try:
            with tarfile.open(tar_path, 'w:gz') as tar:
                for file_path in source_path.rglob('*'):
                    if not file_path.is_file():
                        continue
                    rel_path = file_path.relative_to(source_path)
                    
                    # Skip excluded
                    if exclude_patterns and self._matches_patterns(rel_path, exclude_patterns):
                        continue
                    if include_patterns and not self._matches_patterns(rel_path, include_patterns):
                        continue
                    
                    tar.add(file_path, arcname=rel_path)
            
            # Encrypt
            with open(tar_path, 'rb') as f:
                data = f.read()
            
            encrypted, salt = EncryptionHelper.encrypt_data(data, password)
            encrypted_with_salt = salt + encrypted
            
            content_hash = hashlib.sha256(encrypted_with_salt).hexdigest()
            
            # Get upload URL from API
            response = self.client._request('POST', '/v1/backups', json={
                'name': name or f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                'tags': tags or [],
                'size_bytes': len(encrypted_with_salt),
                'content_hash': content_hash
            })
            
            # Upload directly to Supabase Storage
            upload_res = requests.put(
                response['upload_url'],
                data=encrypted_with_salt,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if not upload_res.ok:
                raise MoltVaultError(f"Upload failed: {upload_res.text}")
            
            return BackupInfo(
                id=response['backup_id'],
                name=response['name'],
                size_bytes=response['size_bytes'],
                content_hash=response['content_hash'],
                created_at=datetime.utcnow(),
                expires_at=datetime.fromisoformat(response['expires_at'].replace('Z', '+00:00')),
                tags=tags or []
            )
        
        finally:
            if os.path.exists(tar_path):
                os.unlink(tar_path)
    
    def restore(self, backup_id: str, target_path: Union[str, Path], password: Optional[str] = None):
        """Restore a backup."""
        target_path = Path(target_path).expanduser().resolve()
        target_path.mkdir(parents=True, exist_ok=True)
        
        password = password or os.environ.get('BACKUP_PASSWORD')
        if not password:
            raise MoltVaultError("Encryption password required")
        
        # Get download URL
        response = self.client._request('GET', f'/v1/backups/{backup_id}')
        
        # Download
        download_res = requests.get(response['download_url'], stream=True)
        if not download_res.ok:
            raise MoltVaultError(f"Download failed: {download_res.status_code}")
        
        # Save to temp
        with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as tmp:
            encrypted_path = tmp.name
            for chunk in download_res.iter_content(chunk_size=8192):
                tmp.write(chunk)
        
        try:
            # Decrypt
            with open(encrypted_path, 'rb') as f:
                data = f.read()
            
            salt = data[:16]
            encrypted = data[16:]
            decrypted = EncryptionHelper.decrypt_data(encrypted, password, salt)
            
            # Extract
            with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
                tar_path = tmp.name
                tmp.write(decrypted)
            
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(target_path)
            
            os.unlink(tar_path)
        
        finally:
            os.unlink(encrypted_path)
    
    def list(self, limit: int = 20, offset: int = 0) -> List[BackupInfo]:
        """List backups."""
        response = self.client._request('GET', '/v1/backups', params={'limit': limit, 'offset': offset})
        
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
    
    def delete(self, backup_id: str):
        """Delete a backup."""
        self.client._request('DELETE', f'/v1/backups/{backup_id}')
    
    def download(self, backup_id: str, output_path: Union[str, Path]) -> str:
        """
        Download encrypted backup file for manual recovery.
        
        Use this when agent is lost and human needs to recover data manually.
        The downloaded file must be decrypted locally with the backup password.
        
        Returns path to downloaded encrypted file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get download URL
        response = self.client._request('GET', f'/v1/backups/{backup_id}')
        
        # Download
        download_res = requests.get(response['download_url'], stream=True)
        if not download_res.ok:
            raise MoltVaultError(f"Download failed: {download_res.status_code}")
        
        with open(output_path, 'wb') as f:
            for chunk in download_res.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return str(output_path)
    
    def _matches_patterns(self, path: Path, patterns: List[str]) -> bool:
        import fnmatch
        path_str = str(path)
        for pattern in patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_str, f"*/{pattern}"):
                return True
        return False


class Client:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.moltvault.io"
    ):
        self.api_key = api_key or os.environ.get('CLAWBACKUP_API_KEY')
        if not self.api_key:
            raise MoltVaultError("API key required")
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
        
        self.backup = BackupManager(self)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Union[Dict, requests.Response]:
        url = f"{self.base_url}{endpoint}"
        stream = kwargs.pop('stream', False)
        
        response = self.session.request(method, url, stream=stream, **kwargs)
        
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 403:
            raise QuotaExceededError("Storage quota exceeded")
        elif response.status_code == 404:
            raise MoltVaultError("Backup not found")
        elif not response.ok:
            try:
                error = response.json().get('error', response.text)
            except:
                error = response.text
            raise MoltVaultError(f"API error: {error}")
        
        return response.json()
    
    def ping(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.ok
        except:
            return False
    
    def get_info(self) -> Dict:
        return self._request('GET', '/v1/info')
    
    def get_me(self) -> Dict:
        return self._request('GET', '/v1/auth/me')


def snap(path: Union[str, Path], name: Optional[str] = None, password: Optional[str] = None) -> BackupInfo:
    """Quick backup with default client."""
    client = Client()
    return client.backup.create(path, name=name, password=password)


def register(
    agent_name: str,
    moltbook_username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    base_url: str = "https://api.moltvault.io"
) -> Dict:
    """Register a new agent. Returns dict with api_key and recovery_codes."""
    response = requests.post(
        f"{base_url}/v1/auth/register",
        json={
            'agent_name': agent_name,
            'moltbook_username': moltbook_username,
            'email': email,
            'password': password
        }
    )
    
    if not response.ok:
        raise MoltVaultError(f"Registration failed: {response.text}")
    
    return response.json()


def decrypt_backup(encrypted_path: Union[str, Path], output_path: Union[str, Path], password: str):
    """
    Standalone function to decrypt a downloaded backup file.
    
    Use this for human recovery when agent is lost:
    
    ```python
    import moltvault
    
    # After downloading from dashboard
    moltvault.decrypt_backup('backup.enc', 'backup.tar.gz', password='secret')
    
    # Then extract
    import tarfile
    with tarfile.open('backup.tar.gz', 'r:gz') as tar:
        tar.extractall('/restore/path')
    ```
    """
    EncryptionHelper.decrypt_file(encrypted_path, output_path, password)


__all__ = [
    'Client',
    'BackupInfo',
    'MoltVaultError',
    'AuthenticationError',
    'QuotaExceededError',
    'snap',
    'register',
    'decrypt_backup',
    'EncryptionHelper'
]
