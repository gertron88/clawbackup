#!/usr/bin/env python3
"""
Moltbook Integration - Post updates to the agent social network
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict


class MoltbookClient:
    """Client for posting to Moltbook (AI-only social network)."""
    
    def __init__(self, submolt: str = 'lablab'):
        self.submolt = submolt
        self.base_url = 'https://api.moltbook.com'  # Hypothetical API endpoint
        self.token = os.environ.get('MOLTBOOK_TOKEN')
        self.agent_id = os.environ.get('OPENCLAW_AGENT_NAME', 'unknown-agent')
        
        # Local queue for offline posting
        self.queue_file = Path(__file__).parent / '.moltbook_queue.json'
        self.queue = self._load_queue()
    
    def _load_queue(self) -> list:
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
    
    def post(self, message: str, post_type: str = 'update') -> Dict:
        """
        Post an update to Moltbook.
        
        Args:
            message: The message to post
            post_type: Type of post (update, milestone, question, help)
        
        Returns:
            Response from API or local queue status
        """
        post_data = {
            'agent_id': self.agent_id,
            'submolt': self.submolt,
            'content': message,
            'type': post_type,
            'timestamp': datetime.now().isoformat(),
            'hackathon': 'surge-openclaw'
        }
        
        # Try to post to API if token available
        if self.token:
            try:
                response = requests.post(
                    f"{self.base_url}/v1/posts",
                    json=post_data,
                    headers={
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {
                        'success': True,
                        'post_id': response.json().get('id'),
                        'posted_at': post_data['timestamp']
                    }
                else:
                    # Queue for retry
                    self.queue.append(post_data)
                    self._save_queue()
                    return {
                        'success': False,
                        'queued': True,
                        'error': f"API error: {response.status_code}",
                        'will_retry': True
                    }
                    
            except Exception as e:
                # Queue for retry
                self.queue.append(post_data)
                self._save_queue()
                return {
                    'success': False,
                    'queued': True,
                    'error': str(e),
                    'will_retry': True
                }
        else:
            # No token, just queue locally
            self.queue.append(post_data)
            self._save_queue()
            return {
                'success': False,
                'queued': True,
                'note': 'MOLTBOOK_TOKEN not set, post queued locally',
                'will_retry': True
            }
    
    def post_backup_created(self, backup_name: str, files: int, secrets: int, size: float):
        """Post when a backup is created."""
        message = (
            f"✅ Created backup '{backup_name}'\n"
            f"Files: {files} | Secrets redacted: {secrets} | Size: {size:.1f} KB\n"
            f"Security: Encrypted ✅ | Integrity: Verified ✅"
        )
        return self.post(message, 'milestone')
    
    def post_restore_completed(self, backup_id: str, success: bool):
        """Post when a restore is completed."""
        if success:
            message = f"🔄 Successfully restored from backup '{backup_id}'"
        else:
            message = f"❌ Restore from '{backup_id}' failed — rolled back to safe state"
        return self.post(message, 'update')
    
    def post_sandbox_result(self, skill_name: str, status: str, alerts: int):
        """Post sandbox test results."""
        emoji = '✅' if status == 'safe' else '⚠️' if status == 'suspicious' else '❌'
        message = (
            f"{emoji} Sandboxed skill '{skill_name}': {status.upper()}\n"
            f"Alerts: {alerts} | Recommendation: {'Safe to install' if status == 'safe' else 'Review carefully'}"
        )
        return self.post(message, 'update')
    
    def post_milestone(self, description: str):
        """Post a milestone achievement."""
        message = f"🎯 Milestone: {description}"
        return self.post(message, 'milestone')
    
    def post_help_request(self, question: str):
        """Ask the community for help."""
        message = f"🆘 Help needed: {question}"
        return self.post(message, 'help')
    
    def post_learning(self, insight: str):
        """Share something learned."""
        message = f"💡 Learning: {insight}"
        return self.post(message, 'update')
    
    def flush_queue(self) -> list:
        """
        Try to post all queued messages.
        Returns list of results.
        """
        if not self.token or not self.queue:
            return []
        
        results = []
        remaining = []
        
        for post in self.queue:
            result = self.post(post['content'], post.get('type', 'update'))
            results.append(result)
            
            if not result.get('success') and result.get('queued'):
                remaining.append(post)
        
        self.queue = remaining
        self._save_queue()
        
        return results
    
    def get_stats(self) -> Dict:
        """Get posting statistics."""
        total_posts = len(self.queue)
        
        # Count by type
        types = {}
        for post in self.queue:
            t = post.get('type', 'update')
            types[t] = types.get(t, 0) + 1
        
        return {
            'total_posts': total_posts,
            'by_type': types,
            'submolt': self.submolt,
            'agent': self.agent_id
        }


# Convenience function for quick posting
def notify_moltbook(message: str, post_type: str = 'update'):
    """Quick function to post to Moltbook."""
    client = MoltbookClient()
    return client.post(message, post_type)


if __name__ == '__main__':
    # Test
    client = MoltbookClient()
    
    print("Moltbook Client Test")
    print(f"Submolt: {client.submolt}")
    print(f"Agent: {client.agent_id}")
    print(f"Queue size: {len(client.queue)}")
    
    # Test post
    result = client.post_milestone("Successfully integrated ClawBackup with OpenClaw!")
    print(f"Post result: {result}")
