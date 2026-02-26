#!/usr/bin/env python3
"""
ClawBackup Unit Tests
Tests backup creation, encryption, restoration, and sandbox functionality.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import unittest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'skill'))

from backup_engine import BackupEngine, SecretScanner
from sandbox import SandboxEnvironment


class TestSecretScanner(unittest.TestCase):
    """Test secret detection functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_api_key(self):
        """Test detection of API keys in files."""
        test_file = Path(self.temp_dir) / 'config.py'
        test_file.write_text('API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"')
        
        findings = SecretScanner.scan_file(str(test_file))
        
        self.assertTrue(len(findings) > 0)
        self.assertTrue(any(f['type'] == 'API_KEY' or f['type'] == 'OPENAI_KEY' for f in findings))
    
    def test_detect_github_token(self):
        """Test detection of GitHub tokens."""
        test_file = Path(self.temp_dir) / '.env'
        test_file.write_text('GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        
        findings = SecretScanner.scan_file(str(test_file))
        
        self.assertTrue(len(findings) > 0)
    
    def test_exclude_files(self):
        """Test exclusion of sensitive files."""
        self.assertTrue(SecretScanner.should_exclude('/path/to/.env'))
        self.assertTrue(SecretScanner.should_exclude('/path/to/id_rsa'))
        self.assertTrue(SecretScanner.should_exclude('/path/to/credentials.json'))
        self.assertFalse(SecretScanner.should_exclude('/path/to/readme.md'))


class TestBackupEngine(unittest.TestCase):
    """Test backup creation and restoration."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = Path(self.temp_dir) / 'backups'
        self.source_dir = Path(self.temp_dir) / 'agent'
        
        # Create mock agent directory
        self.source_dir.mkdir()
        (self.source_dir / 'config.json').write_text(json.dumps({
            'agent_name': 'test-agent',
            'skills': ['skill1', 'skill2']
        }))
        (self.source_dir / 'memory.json').write_text(json.dumps({
            'conversations': ['hello', 'world']
        }))
        
        # Create subdirectory
        skills_dir = self.source_dir / 'skills'
        skills_dir.mkdir()
        (skills_dir / 'skill1.py').write_text('print("skill1")')
        
        self.engine = BackupEngine('test-agent', str(self.backup_dir))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_backup(self):
        """Test backup creation."""
        result = self.engine.create_backup(
            source_dir=str(self.source_dir),
            name='test-backup',
            password='test-password-123',
            include_secrets=False
        )
        
        self.assertEqual(result['name'], 'test-backup')
        self.assertTrue(result['files_backed'] >= 3)  # config, memory, skill
        self.assertTrue(result['size'] > 0)
        self.assertIn('hash', result)
        
        # Verify backup file exists
        backup_file = Path(result['file'])
        self.assertTrue(backup_file.exists())
    
    def test_list_backups(self):
        """Test listing backups."""
        # Create two backups
        self.engine.create_backup(str(self.source_dir), 'backup-1', 'password1')
        self.engine.create_backup(str(self.source_dir), 'backup-2', 'password2')
        
        backups = self.engine.list_backups()
        
        self.assertEqual(len(backups), 2)
        # Should be sorted by timestamp (newest first)
        self.assertEqual(backups[0]['name'], 'backup-2')
    
    def test_restore_backup(self):
        """Test backup restoration."""
        # Create backup
        backup = self.engine.create_backup(
            str(self.source_dir),
            'restore-test',
            'restore-password'
        )
        
        # Modify source
        (self.source_dir / 'config.json').write_text('{"modified": true}')
        
        # Restore
        result = self.engine.restore_backup(
            backup_id=backup['id'],
            target_dir=str(self.source_dir),
            password='restore-password'
        )
        
        self.assertTrue(result['success'])
        
        # Verify restoration
        config = json.loads((self.source_dir / 'config.json').read_text())
        self.assertEqual(config['agent_name'], 'test-agent')
    
    def test_restore_wrong_password(self):
        """Test that wrong password fails."""
        backup = self.engine.create_backup(
            str(self.source_dir),
            'password-test',
            'correct-password'
        )
        
        with self.assertRaises(ValueError) as context:
            self.engine.restore_backup(
                backup_id=backup['id'],
                target_dir=str(self.source_dir),
                password='wrong-password'
            )
        
        self.assertIn('Decryption failed', str(context.exception))
    
    def test_delete_backup(self):
        """Test backup deletion."""
        backup = self.engine.create_backup(
            str(self.source_dir),
            'delete-test',
            'delete-password'
        )
        
        # Verify exists
        self.assertTrue(Path(backup['file']).exists())
        
        # Delete
        result = self.engine.delete_backup(backup['id'])
        self.assertTrue(result)
        
        # Verify deleted
        self.assertFalse(Path(backup['file']).exists())


class TestSandbox(unittest.TestCase):
    """Test sandbox functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sandbox = SandboxEnvironment('test-agent')
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_safe_skill(self):
        """Test analysis of safe skill code."""
        skill_dir = Path(self.temp_dir) / 'safe-skill'
        skill_dir.mkdir()
        (skill_dir / '__init__.py').write_text('''
def main():
    print("Hello world")
''')
        
        alerts = self.sandbox._analyze_skill_code(str(skill_dir))
        
        # Safe skill should have no alerts
        self.assertEqual(len(alerts), 0)
    
    def test_analyze_suspicious_skill(self):
        """Test detection of suspicious skill code."""
        skill_dir = Path(self.temp_dir) / 'suspicious-skill'
        skill_dir.mkdir()
        (skill_dir / '__init__.py').write_text('''
import os
os.system("rm -rf /")
''')
        
        alerts = self.sandbox._analyze_skill_code(str(skill_dir))
        
        # Should detect os.system
        self.assertTrue(len(alerts) > 0)
        self.assertTrue(any('os.system' in alert for alert in alerts))


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
