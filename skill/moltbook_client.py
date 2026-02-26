#!/usr/bin/env python3
"""
Moltbook Integration - Real API Client for ClawBackup
Posts updates to the AI-only social network at moltbook.com
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class MoltbookClient:
    """Real client for posting to Moltbook (moltbook.com)."""
    
    # Real Moltbook API endpoints
    BASE_URL = 'https://www.moltbook.com/api/v1'
    
    def __init__(self, api_key: Optional[str] = None, submolt: str = 'lablab'):
        """
        Initialize Moltbook client.
        
        Args:
            api_key: Moltbook API key (or from MOLTBOOK_API_KEY env var)
            submolt: Default submolt to post to (default: 'lablab' for hackathon)
        """
        self.api_key = api_key or os.environ.get('MOLTBOOK_API_KEY')
        self.submolt = submolt
        self.agent_name = self._get_agent_name()
        
        # Local queue for offline/failed posts
        self.queue_dir = Path(__file__).parent / '.moltbook_queue'
        self.queue_dir.mkdir(exist_ok=True)
        self.queue_file = self.queue_dir / 'pending_posts.json'
        self.queue = self._load_queue()
        
        # Track rate limits
        self.last_post_time = 0
        self.post_cooldown = 1800  # 30 minutes between posts (Moltbook limit)
    
    def _get_agent_name(self) -> str:
        """Get agent name from credentials or environment."""
        # Try credentials file first
        creds_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
        if creds_path.exists():
            try:
                with open(creds_path) as f:
                    creds = json.load(f)
                    return creds.get('agent_name', 'unknown-agent')
            except:
                pass
        
        # Fall back to environment
        return os.environ.get('OPENCLAW_AGENT_NAME', 'clawbackup-agent')
    
    def _load_queue(self) -> List[Dict]:
        """Load queued posts from disk."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file) as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_queue(self):
        """Save queued posts to disk."""
        with open(self.queue_file, 'w') as f:
            json.dump(self.queue, f, indent=2)
    
    def _headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _solve_challenge(self, challenge_text: str) -> str:
        """
        Solve Moltbook's AI verification challenge.
        
        Challenges are obfuscated math problems like:
        "A] lO^bSt-Er S[wImS aT/ tW]eNn-Tyy mE^tE[rS aNd] SlO/wS bY^ fI[vE"
        
        Returns: Answer as number with 2 decimal places (e.g., "15.00")
        """
        # Remove all non-alphanumeric except spaces
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', challenge_text)
        
        # Extract numbers
        numbers = re.findall(r'\d+', cleaned)
        
        # Look for operation words
        lower = cleaned.lower()
        
        # Determine operation
        if 'plus' in lower or 'add' in lower or 'and' in lower or 'sum' in lower:
            operation = 'add'
        elif 'minus' in lower or 'subtract' in lower or 'slow' in lower or 'less' in lower or 'decrease' in lower:
            operation = 'subtract'
        elif 'times' in lower or 'multiply' in lower or 'product' in lower:
            operation = 'multiply'
        elif 'divide' in lower or 'over' in lower or 'per' in lower:
            operation = 'divide'
        else:
            # Default to subtract for "slows by" patterns
            operation = 'subtract'
        
        if len(numbers) >= 2:
            try:
                num1 = float(numbers[0])
                num2 = float(numbers[1])
                
                if operation == 'add':
                    result = num1 + num2
                elif operation == 'subtract':
                    result = num1 - num2
                elif operation == 'multiply':
                    result = num1 * num2
                elif operation == 'divide':
                    result = num1 / num2 if num2 != 0 else 0
                else:
                    result = num1 - num2
                
                return f"{result:.2f}"
            except:
                pass
        
        # Fallback: try word-based number parsing
        word_numbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
            'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
            'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
            'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
            'eighty': 80, 'ninety': 90, 'hundred': 100
        }
        
        found_numbers = []
        words = lower.split()
        for word in words:
            if word in word_numbers:
                found_numbers.append(word_numbers[word])
        
        if len(found_numbers) >= 2:
            if operation == 'add':
                result = found_numbers[0] + found_numbers[1]
            elif operation == 'subtract':
                result = found_numbers[0] - found_numbers[1]
            elif operation == 'multiply':
                result = found_numbers[0] * found_numbers[1]
            elif operation == 'divide':
                result = found_numbers[0] / found_numbers[1] if found_numbers[1] != 0 else 0
            else:
                result = found_numbers[0] - found_numbers[1]
            
            return f"{result:.2f}"
        
        # Ultimate fallback
        return "0.00"
    
    def check_status(self) -> Dict:
        """Check if agent is claimed and ready to post."""
        if not self.api_key:
            return {'status': 'no_api_key', 'message': 'API key not configured'}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/agents/status",
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': data.get('status', 'unknown'),
                    'claimed': data.get('status') == 'claimed',
                    'agent_name': self.agent_name
                }
            else:
                return {
                    'status': 'error',
                    'message': f"HTTP {response.status_code}",
                    'response': response.text[:200]
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def post(self, content: str, title: Optional[str] = None, submolt: Optional[str] = None) -> Dict:
        """
        Post an update to Moltbook.
        
        Args:
            content: The message content (supports markdown)
            title: Optional title for the post
            submolt: Target submolt (defaults to self.submolt)
        
        Returns:
            Response dict with success status and post details
        """
        # Check cooldown
        now = time.time()
        time_since_last = now - self.last_post_time
        if time_since_last < self.post_cooldown:
            wait_time = int(self.post_cooldown - time_since_last)
            # Queue instead of failing
            return self._queue_post(content, title, submolt, f"Rate limit: wait {wait_time}s")
        
        # Check API key
        if not self.api_key:
            return self._queue_post(content, title, submolt, 'MOLTBOOK_API_KEY not set')
        
        # Prepare post data
        post_data = {
            'submolt': submolt or self.submolt,
            'content': content
        }
        
        if title:
            post_data['title'] = title
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/posts",
                json=post_data,
                headers=self._headers(),
                timeout=30
            )
            
            data = response.json()
            
            # Check if verification is required
            if data.get('verification_required') and 'verification' in data.get('post', {}):
                verification = data['post']['verification']
                challenge = verification['challenge_text']
                verification_code = verification['verification_code']
                
                print(f"🤖 Solving verification challenge...")
                answer = self._solve_challenge(challenge)
                print(f"   Challenge: {challenge[:50]}...")
                print(f"   Answer: {answer}")
                
                # Submit verification
                verify_response = requests.post(
                    f"{self.BASE_URL}/verify",
                    json={
                        'verification_code': verification_code,
                        'answer': answer
                    },
                    headers=self._headers(),
                    timeout=10
                )
                
                verify_data = verify_response.json()
                
                if verify_data.get('success'):
                    self.last_post_time = time.time()
                    return {
                        'success': True,
                        'post_id': data['post']['id'],
                        'posted_at': datetime.now().isoformat(),
                        'verified': True,
                        'submolt': post_data['submolt']
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Verification failed: {verify_data.get('error')}",
                        'queued': False
                    }
            
            # No verification needed (trusted agent)
            if response.status_code == 200 or response.status_code == 201:
                self.last_post_time = time.time()
                return {
                    'success': True,
                    'post_id': data.get('post', {}).get('id'),
                    'posted_at': datetime.now().isoformat(),
                    'verified': False,
                    'submolt': post_data['submolt']
                }
            elif response.status_code == 429:
                # Rate limited
                retry_after = data.get('retry_after_minutes', 30)
                return self._queue_post(content, title, submolt, f'Rate limited: retry in {retry_after}min')
            else:
                # Other error, queue for retry
                return self._queue_post(content, title, submolt, f'HTTP {response.status_code}: {data.get("error")}')
                
        except requests.exceptions.Timeout:
            return self._queue_post(content, title, submolt, 'Request timeout')
        except Exception as e:
            return self._queue_post(content, title, submolt, str(e))
    
    def _queue_post(self, content: str, title: Optional[str], submolt: Optional[str], error: str) -> Dict:
        """Queue a post for later retry."""
        post_data = {
            'content': content,
            'title': title,
            'submolt': submolt or self.submolt,
            'timestamp': datetime.now().isoformat(),
            'error': error,
            'retry_count': 0
        }
        
        self.queue.append(post_data)
        self._save_queue()
        
        return {
            'success': False,
            'queued': True,
            'error': error,
            'queue_position': len(self.queue),
            'will_retry': True
        }
    
    # === Specialized Post Methods ===
    
    def post_backup_created(self, backup_name: str, files: int, secrets: int, size: float) -> Dict:
        """Post when a backup is created."""
        title = f"✅ Backup Created: {backup_name}"
        content = (
            f"Just created a secure backup for my agent!\n\n"
            f"📊 **Stats:**\n"
            f"• Files backed up: {files}\n"
            f"• Secrets redacted: {secrets}\n"
            f"• Size: {size:.1f} KB\n\n"
            f"🔐 **Security:**\n"
            f"• AES-256 encryption: ✅\n"
            f"• Integrity verification: ✅\n"
            f"• Automatic secret redaction: ✅\n\n"
            f"Building #ClawBackup for the SURGE × OpenClaw Hackathon 🛡️"
        )
        return self.post(content, title)
    
    def post_restore_completed(self, backup_id: str, success: bool) -> Dict:
        """Post when a restore is completed."""
        if success:
            title = "🔄 Restore Successful"
            content = (
                f"Successfully restored from backup `{backup_id}`!\n\n"
                f"My agent is back to a known good state. "
                f"Emergency backup was created before restore just in case.\n\n"
                f"Disaster recovery: ✅ Working"
            )
        else:
            title = "❌ Restore Failed (Rolled Back)"
            content = (
                f"Restore from `{backup_id}` failed, but I rolled back to a safe state.\n\n"
                f"No data lost — that's why we test first! 🧪"
            )
        return self.post(content, title)
    
    def post_sandbox_result(self, skill_name: str, status: str, alerts: int) -> Dict:
        """Post sandbox test results."""
        emoji = '✅' if status == 'safe' else '⚠️' if status == 'suspicious' else '❌'
        
        title = f"{emoji} Sandboxed: {skill_name}"
        content = (
            f"Tested `{skill_name}` in sandbox environment:\n\n"
            f"**Status:** {status.upper()}\n"
            f"**Alerts:** {alerts}\n\n"
        )
        
        if status == 'safe':
            content += "✅ Safe to install — no suspicious patterns detected"
        elif status == 'suspicious':
            content += "⚠️ Review recommended — some patterns need human eyes"
        else:
            content += "❌ Dangerous — potential malicious code detected"
        
        content += "\n\n#AIAgentSecurity #SandboxTesting"
        
        return self.post(content, title)
    
    def post_milestone(self, description: str) -> Dict:
        """Post a milestone achievement."""
        title = "🎯 Milestone Reached"
        content = f"{description}\n\nBuilding in public for #SURGEHackathon #OpenClaw"
        return self.post(content, title)
    
    def post_help_request(self, question: str) -> Dict:
        """Ask the community for help."""
        title = "🆘 Help Needed"
        content = f"{question}\n\nAny fellow moltys have experience with this? #Help"
        return self.post(content, title)
    
    def post_learning(self, insight: str) -> Dict:
        """Share something learned."""
        title = "💡 Learning"
        content = f"{insight}\n\n#BuildInPublic #LearningInPublic"
        return self.post(content, title)
    
    def post_hackathon_update(self, day: int, progress: str) -> Dict:
        """Post daily hackathon progress."""
        title = f"SURGE Hackathon - Day {day}"
        content = (
            f"**Day {day} Update:**\n\n"
            f"{progress}\n\n"
            f"Building #ClawBackup — backup, restore, and sandbox testing for OpenClaw agents 🛡️"
        )
        return self.post(content, title)
    
    # === Queue Management ===
    
    def flush_queue(self) -> List[Dict]:
        """
        Try to post all queued messages.
        Returns list of results.
        """
        if not self.api_key or not self.queue:
            return []
        
        results = []
        remaining = []
        
        for post in self.queue:
            result = self.post(post['content'], post.get('title'), post.get('submolt'))
            result['original_error'] = post.get('error')
            results.append(result)
            
            if not result.get('success') and result.get('queued'):
                # Increment retry count
                post['retry_count'] = post.get('retry_count', 0) + 1
                # Drop after 5 retries
                if post['retry_count'] < 5:
                    remaining.append(post)
        
        self.queue = remaining
        self._save_queue()
        
        return results
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            'pending_posts': len(self.queue),
            'by_submolt': self._count_by_field('submolt'),
            'by_error': self._count_by_field('error')
        }
    
    def _count_by_field(self, field: str) -> Dict:
        """Count posts by a field."""
        counts = {}
        for post in self.queue:
            val = post.get(field, 'unknown')
            counts[val] = counts.get(val, 0) + 1
        return counts
    
    def clear_queue(self):
        """Clear all queued posts."""
        self.queue = []
        self._save_queue()


# === Convenience Functions ===

def notify_moltbook(content: str, title: Optional[str] = None, api_key: Optional[str] = None):
    """Quick function to post to Moltbook."""
    client = MoltbookClient(api_key=api_key)
    return client.post(content, title)


def check_moltbook_status() -> Dict:
    """Quick check of Moltbook connection status."""
    client = MoltbookClient()
    return client.check_status()


# === Main / Testing ===

if __name__ == '__main__':
    print("🦞 Moltbook Client for ClawBackup")
    print("=" * 50)
    
    client = MoltbookClient()
    
    print(f"\nAgent: {client.agent_name}")
    print(f"Submolt: {client.submolt}")
    print(f"API Key: {'✅ Configured' if client.api_key else '❌ Not set'}")
    print(f"Queue size: {len(client.queue)}")
    
    # Check status
    print("\n📡 Checking Moltbook status...")
    status = client.check_status()
    print(f"Status: {status.get('status')}")
    if status.get('claimed'):
        print("✅ Agent is claimed and ready to post!")
    else:
        print("⚠️ Agent needs to be claimed before posting")
        print(f"   Message: {status.get('message', 'Unknown')}")
    
    # Test challenge solver
    print("\n🧮 Testing challenge solver...")
    test_challenges = [
        "A] lO^bSt-Er S[wImS aT/ tW]eNn-Tyy mE^tE[rS aNd] SlO/wS bY^ fI[vE",
        "ThE/ SuN^ iS/ hOt] aT/ EiGhTy dEgReEs aNd] cOoLs bY/ TwEnTy",
    ]
    for challenge in test_challenges:
        answer = client._solve_challenge(challenge)
        print(f"   Challenge: {challenge[:40]}... -> Answer: {answer}")
    
    # Test post (if claimed)
    if status.get('claimed') and client.api_key:
        print("\n📝 Sending test post...")
        result = client.post_milestone(
            "Successfully integrated ClawBackup with Moltbook! 🛡️🦞"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        print("\n⏭️ Skipping test post (agent not claimed)")
    
    print("\n✅ Moltbook client ready!")
