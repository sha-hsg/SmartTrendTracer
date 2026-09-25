"""
Shared state, imports, and classes for tag reorganization package
"""

from typing import Dict
from datetime import datetime, timezone
import logging

from app.repositories import tag_reorganization_utils_queries as queries

logger = logging.getLogger(__name__)

# Store active reorganization tasks (for real-time updates)
active_tasks: Dict[str, Dict] = {}

class ReorganizationTask:
    def __init__(self, task_id: str, mode: str):
        self.task_id = task_id
        self.mode = mode
        self.status = "initializing"
        self.progress = 0
        self.current_step = ""
        self.messages = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time = None
        self.result = None
        self.error = None
        self.cancelled = False
        self.total_steps = 0
        self.completed_steps = 0
        self.debug_prompt = ""
        self.debug_system_prompt = ""

        # Save initial state to MongoDB
        self._save_to_db()

    def _save_to_db(self):
        """Save current task state to MongoDB"""
        doc = {
            'task_id': self.task_id,
            'status': self.status,
            'mode': self.mode,
            'created_at': self.start_time,
            'updated_at': datetime.now(timezone.utc),
            'completed_at': self.end_time,
            'progress': {
                'current': self.progress,
                'total': self.total_steps,
                'completed_steps': self.completed_steps,
                'current_step': self.current_step,
                'messages': [{'time': msg.get('time'), 'text': msg.get('text')} for msg in self.messages[-20:]]  # Keep last 20 messages
            },
            'result': self.result,
            'error': self.error,
            'cancelled': self.cancelled,
            'debug_info': {
                'prompt': self.debug_prompt[:1000] if self.debug_prompt else None,  # Store first 1000 chars
                'system_prompt': self.debug_system_prompt[:1000] if self.debug_system_prompt else None,
                'prompt_size': len(self.debug_prompt) if self.debug_prompt else 0,
                'system_prompt_size': len(self.debug_system_prompt) if self.debug_system_prompt else 0
            },
            'metadata': {
                'processing_time_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
                'concepts_count': getattr(self, 'concepts_count', 0),
                'organized_count': getattr(self, 'organized_count', 0),
                'unorganized_count': getattr(self, 'unorganized_count', 0)
            }
        }

        # Upsert to MongoDB
        queries.tag_reorganization_tasks_replace_one___save_to_db(doc, self)

    def update(self, status: str = None, progress: int = None,
               current_step: str = None, message: str = None):
        if status:
            self.status = status
        if progress is not None:
            self.progress = progress
        if current_step:
            self.current_step = current_step
        if message:
            self.messages.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "text": message
            })

        # Save updates to MongoDB
        self._save_to_db()

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "mode": self.mode,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "messages": self.messages[-10:],  # Keep last 10 messages
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "elapsed_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds() if self.start_time else 0,
            "cancelled": self.cancelled,
            "error": self.error,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "debug_prompt": self.debug_prompt[:1000] if self.debug_prompt else "",  # First 1000 chars for preview
            "debug_prompt_full_size": len(self.debug_prompt) if self.debug_prompt else 0
        }
