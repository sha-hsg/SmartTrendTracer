"""
Persistent rate limiter that remembers state across restarts
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PersistentRateLimiter:
    """Rate limiter that persists state to disk"""
    
    def __init__(self, state_file="data/rate_limit_state.json"):
        self.state_file = Path(state_file)
        self.window_minutes = 15
        self.max_requests = 10
        
        # Ensure data directory exists
        self.state_file.parent.mkdir(exist_ok=True)
        
        # Load state from disk
        self.load_state()
    
    def load_state(self):
        """Load rate limiter state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                # Parse timestamps
                self.requests_made = [
                    datetime.fromisoformat(ts) for ts in state.get('requests_made', [])
                ]
                
                # Parse backoff time
                backoff_until_str = state.get('backoff_until')
                if backoff_until_str:
                    self.backoff_until = datetime.fromisoformat(backoff_until_str)
                else:
                    self.backoff_until = None
                
                # Parse last 429 time
                last_429_str = state.get('last_429_time')
                if last_429_str:
                    self.last_429_time = datetime.fromisoformat(last_429_str)
                else:
                    self.last_429_time = None
                
                logger.info(f"Loaded rate limiter state: {len(self.requests_made)} requests in window")
                if self.backoff_until:
                    logger.info(f"Backoff until: {self.backoff_until}")
                    
            except Exception as e:
                logger.error(f"Failed to load rate limiter state: {e}")
                self.reset()
        else:
            self.reset()
    
    def save_state(self):
        """Save rate limiter state to disk"""
        try:
            state = {
                'requests_made': [ts.isoformat() for ts in self.requests_made],
                'backoff_until': self.backoff_until.isoformat() if self.backoff_until else None,
                'last_429_time': self.last_429_time.isoformat() if self.last_429_time else None,
                'saved_at': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.debug("Saved rate limiter state")
            
        except Exception as e:
            logger.error(f"Failed to save rate limiter state: {e}")
    
    def can_make_request(self):
        """Check if we can make a request without hitting rate limit"""
        now = datetime.now(timezone.utc)
        
        # If we're in backoff period, wait
        if self.backoff_until and now < self.backoff_until:
            wait_seconds = (self.backoff_until - now).total_seconds()
            logger.info(f"Rate limit backoff: waiting {wait_seconds:.0f} seconds")
            return False
        
        # Clean old requests outside the window
        window_start = now - timedelta(minutes=self.window_minutes)
        self.requests_made = [req_time for req_time in self.requests_made 
                              if req_time > window_start]
        
        # Check if we can make a request
        if len(self.requests_made) < self.max_requests:
            return True
        
        # Calculate how long to wait
        oldest_request = min(self.requests_made)
        wait_until = oldest_request + timedelta(minutes=self.window_minutes)
        wait_seconds = (wait_until - now).total_seconds()
        
        if wait_seconds > 0:
            logger.info(f"Rate limit: {len(self.requests_made)}/{self.max_requests} requests in last {self.window_minutes} min")
            logger.info(f"Need to wait {wait_seconds:.0f} seconds")
            return False
        
        return True
    
    def record_request(self):
        """Record that a request was made"""
        self.requests_made.append(datetime.now(timezone.utc))
        logger.debug(f"Request recorded. Total in window: {len(self.requests_made)}")
        self.save_state()
    
    def handle_429_error(self):
        """Handle a 429 Too Many Requests error"""
        now = datetime.now(timezone.utc)
        self.last_429_time = now
        
        # Always wait full 15 minutes as requested by user
        new_backoff = 900  # 15 minutes
        
        self.backoff_until = now + timedelta(seconds=new_backoff)
        logger.warning(f"Got 429 error. Backing off for {new_backoff} seconds (15 minutes) until {self.backoff_until}")
        
        self.save_state()
        return new_backoff
    
    def reset(self):
        """Reset the rate limiter"""
        self.requests_made = []
        self.backoff_until = None
        self.last_429_time = None
        self.save_state()
    
    def clear_backoff(self):
        """Clear the backoff period (for manual override)"""
        self.backoff_until = None
        logger.info("Cleared rate limit backoff")
        self.save_state()
    
    def get_wait_time(self):
        """Calculate how long to wait before next request can be made"""
        now = datetime.now(timezone.utc)
        
        # If we're in backoff period, return remaining backoff time
        if self.backoff_until and now < self.backoff_until:
            return (self.backoff_until - now).total_seconds()
        
        # Clean old requests outside the window
        window_start = now - timedelta(minutes=self.window_minutes)
        self.requests_made = [req_time for req_time in self.requests_made 
                              if req_time > window_start]
        
        # If we can make a request now, no wait needed
        if len(self.requests_made) < self.max_requests:
            return 0
        
        # Calculate how long to wait until oldest request expires
        oldest_request = min(self.requests_made)
        wait_until = oldest_request + timedelta(minutes=self.window_minutes)
        wait_seconds = (wait_until - now).total_seconds()
        
        return max(0, wait_seconds)

# Global persistent rate limiter instance
_persistent_limiter = None

def get_persistent_rate_limiter():
    """Get the global persistent rate limiter instance"""
    global _persistent_limiter
    if _persistent_limiter is None:
        _persistent_limiter = PersistentRateLimiter()
    return _persistent_limiter