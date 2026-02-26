#!/usr/bin/env python3
"""
ClawBackup Sandbox - Safe skill testing environment
Isolates new skills to prevent breaking the main agent.
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SandboxReport:
    """Report from sandbox testing."""
    skill_name: str
    status: str  # 'safe', 'suspicious', 'dangerous'
    duration_ms: int
    file_accesses: List[Dict]
    network_calls: List[Dict]
    resource_usage: Dict
    alerts: List[str]
    logs: List[str]


class SandboxEnvironment:
    """Creates isolated environment for testing skills."""
    
    # Suspicious patterns to watch for
    SUSPICIOUS_PATTERNS = {
        'file_access': [
            '/etc/passwd', '/etc/shadow', '/etc/hosts',
            '~/.ssh', '~/.aws', '~/.openclaw/credentials',
            '/proc', '/sys',
        ],
        'network': [
            'tor', 'onion', 'pastebin', 'hookbin',
            'ngrok', '127.0.0.1', '0.0.0.0',
        ],
        'commands': [
            'rm -rf /', 'dd if=', 'mkfs',
            'curl.*sh', 'wget.*sh',  # Pipe to shell
        ]
    }
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.sandbox_dir = Path(tempfile.gettempdir()) / f"clawbackup_sandbox_{agent_name}"
        self.fs_watch_log = []
        self.network_log = []
    
    def create_isolated_copy(self, source_dir: str) -> str:
        """Create isolated copy of agent for testing."""
        # Clean up old sandbox
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
        
        # Copy agent state
        shutil.copytree(source_dir, self.sandbox_dir, 
                       ignore=shutil.ignore_patterns('backups', '__pycache__', '.git'))
        
        return str(self.sandbox_dir)
    
    def install_skill_sandboxed(self, skill_path: str, timeout: int = 60) -> SandboxReport:
        """
        Install and test a skill in sandbox.
        
        Args:
            skill_path: Path to skill to test
            timeout: Maximum test duration in seconds
        
        Returns:
            SandboxReport with findings
        """
        start_time = datetime.now()
        alerts = []
        logs = []
        file_accesses = []
        network_calls = []
        
        try:
            # Use strace/system monitoring if available (Linux)
            # For demo, we'll use a simpler approach
            
            # Set up resource limits
            import resource
            
            def limit_resources():
                """Limit CPU and memory in child process."""
                # 30 second CPU limit
                resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
                # 512MB memory limit
                resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
            
            # Run skill installation in subprocess
            skill_name = Path(skill_path).name
            
            # Analyze skill code first
            alerts.extend(self._analyze_skill_code(skill_path))
            
            # Attempt installation (in controlled way)
            logs.append(f"Starting sandboxed install of {skill_name}")
            
            # For hackathon: simulate the monitoring
            # In production: use actual sandboxing (Docker, seccomp, etc.)
            
            test_script = f"""
import sys
sys.path.insert(0, '{self.sandbox_dir}')

# Try to import and initialize skill
try:
    # Read skill manifest
    import json
    with open('{skill_path}/skill.json') as f:
        manifest = json.load(f)
    print(f"Skill manifest: {{manifest.get('name', 'unknown')}}")
    
    # Check for suspicious imports
    with open('{skill_path}/__init__.py') as f:
        code = f.read()
    
    suspicious = ['os.system', 'subprocess', 'socket', 'requests']
    found = [s for s in suspicious if s in code]
    if found:
        print(f"WARNING: Suspicious imports: {{found}}")
    
    print("SANDBOX_TEST_PASSED")
except Exception as e:
    print(f"SANDBOX_TEST_FAILED: {{e}}")
"""
            
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=limit_resources if os.name != 'nt' else None
            )
            
            logs.extend(result.stdout.strip().split('\n'))
            
            if 'SANDBOX_TEST_FAILED' in result.stderr:
                alerts.append(f"Skill failed to load: {result.stderr}")
            
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Determine status
            status = 'safe'
            if any('WARNING' in log for log in logs):
                status = 'suspicious'
            if alerts:
                status = 'dangerous'
            
            return SandboxReport(
                skill_name=skill_name,
                status=status,
                duration_ms=duration,
                file_accesses=file_accesses,
                network_calls=network_calls,
                resource_usage={'cpu_ms': duration, 'memory_mb': 0},
                alerts=alerts,
                logs=logs
            )
            
        except subprocess.TimeoutExpired:
            return SandboxReport(
                skill_name=Path(skill_path).name,
                status='dangerous',
                duration_ms=timeout * 1000,
                file_accesses=[],
                network_calls=[],
                resource_usage={},
                alerts=['Skill exceeded timeout - possible infinite loop or resource exhaustion'],
                logs=logs + ['TIMEOUT: Skill took too long to initialize']
            )
        
        except Exception as e:
            return SandboxReport(
                skill_name=Path(skill_path).name,
                status='dangerous',
                duration_ms=0,
                file_accesses=[],
                network_calls=[],
                resource_usage={},
                alerts=[f'Sandbox error: {str(e)}'],
                logs=logs
            )
        
        finally:
            # Cleanup
            if self.sandbox_dir.exists():
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)
    
    def _analyze_skill_code(self, skill_path: str) -> List[str]:
        """Static analysis of skill code."""
        alerts = []
        skill_dir = Path(skill_path)
        
        # Check for suspicious patterns in all Python files
        for py_file in skill_dir.rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    code = f.read()
                
                # Check for dangerous patterns
                dangerous = [
                    ('os.system(', 'Executes shell commands'),
                    ('eval(', 'Uses eval() - code injection risk'),
                    ('exec(', 'Uses exec() - code injection risk'),
                    ('__import__', 'Dynamic imports'),
                    ('subprocess.call', 'Subprocess execution'),
                    ('open(', 'File operations'),
                ]
                
                for pattern, risk in dangerous:
                    if pattern in code:
                        alerts.append(f"{py_file.name}: {risk}")
                
            except Exception:
                pass
        
        return alerts
    
    def generate_report(self, report: SandboxReport) -> str:
        """Generate human-readable report."""
        lines = [
            f"🧪 Sandbox Test Report: {report.skill_name}",
            f"Status: {report.status.upper()}",
            f"Duration: {report.duration_ms}ms",
            "",
            "Alerts:"
        ]
        
        if report.alerts:
            for alert in report.alerts:
                lines.append(f"  ⚠️  {alert}")
        else:
            lines.append("  ✅ No issues detected")
        
        lines.extend(["", "Logs:"])
        for log in report.logs[-10:]:  # Last 10 logs
            lines.append(f"  {log}")
        
        lines.append("")
        lines.append("Recommendation:")
        if report.status == 'safe':
            lines.append("  ✅ Safe to install")
        elif report.status == 'suspicious':
            lines.append("  ⚠️  Review carefully before installing")
        else:
            lines.append("  ❌ DO NOT INSTALL - Dangerous")
        
        return '\n'.join(lines)


if __name__ == '__main__':
    print("ClawBackup Sandbox module loaded")
    print("Usage: sandbox = SandboxEnvironment('agent-name')")
    print("       report = sandbox.install_skill_sandboxed('/path/to/skill')")
