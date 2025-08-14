"""
Rate limiter for Twitter API calls
Handles 429 errors and implements smart backoff
"""
import time
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class TwitterRateLimiter:
    """
    Twitter API Rate Limiter
    Basic tier: 10 requests per 15 minutes
    """
    
    def __init__(self):
        self.requests_made = []
        self.window_minutes = 15
        self.max_requests = 10  # Twitter Basic tier limit
        self.last_429_time = None
        self.backoff_until = None
        
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
    
    def handle_429_error(self):
        """Handle a 429 Too Many Requests error"""
        now = datetime.now(timezone.utc)
        self.last_429_time = now
        
        # Always wait full 15 minutes as requested by user
        # This ensures we respect the rate limit window fully
        new_backoff = 900  # Always 15 minutes (900 seconds)
        
        self.backoff_until = now + timedelta(seconds=new_backoff)
        logger.warning(f"Got 429 error. Backing off for {new_backoff} seconds (15 minutes) until {self.backoff_until}")
        
        return new_backoff
    
    def wait_if_needed(self):
        """Wait if necessary before making a request"""
        while not self.can_make_request():
            now = datetime.now(timezone.utc)
            
            if self.backoff_until and now < self.backoff_until:
                wait_seconds = (self.backoff_until - now).total_seconds()
                print(f"⏳ Rate limited. Waiting {wait_seconds:.0f} seconds...")
                time.sleep(min(wait_seconds, 60))  # Check every minute
            else:
                # Calculate wait based on window
                window_start = now - timedelta(minutes=self.window_minutes)
                self.requests_made = [req_time for req_time in self.requests_made 
                                      if req_time > window_start]
                
                if len(self.requests_made) >= self.max_requests:
                    oldest_request = min(self.requests_made)
                    wait_until = oldest_request + timedelta(minutes=self.window_minutes)
                    wait_seconds = (wait_until - now).total_seconds()
                    
                    if wait_seconds > 0:
                        print(f"⏳ Rate limit reached ({self.max_requests} requests). Waiting {wait_seconds:.0f} seconds...")
                        time.sleep(min(wait_seconds + 1, 60))  # Add 1 second buffer
                else:
                    break
    
    def reset(self):
        """Reset the rate limiter"""
        self.requests_made = []
        self.backoff_until = None
        self.last_429_time = None

# Global rate limiter instance
rate_limiter = TwitterRateLimiter()

def get_rate_limiter():
    """Get the global rate limiter instance"""
    return rate_limiter