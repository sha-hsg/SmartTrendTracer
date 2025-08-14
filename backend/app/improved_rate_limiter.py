"""
Improved rate limiter with proper shutdown handling
"""
import time
import threading
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class ImprovedRateLimiter:
    """
    Twitter API Rate Limiter with shutdown support
    Basic tier: 10 requests per 15 minutes
    """
    
    def __init__(self):
        self.requests_made = []
        self.window_minutes = 15
        self.max_requests = 10  # Twitter Basic tier limit
        self.last_429_time = None
        self.backoff_until = None
        self._shutdown = threading.Event()
        
    def shutdown(self):
        """Signal shutdown to stop waiting"""
        logger.info("Rate limiter shutdown requested")
        self._shutdown.set()
    
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
        
        # Exponential backoff: start with 5 minutes, max 15 minutes
        if self.backoff_until and self.backoff_until > now:
            # Already in backoff, double the wait time
            current_backoff = (self.backoff_until - now).total_seconds()
            new_backoff = min(current_backoff * 2, 900)  # Max 15 minutes
        else:
            new_backoff = 300  # Start with 5 minutes
        
        self.backoff_until = now + timedelta(seconds=new_backoff)
        logger.warning(f"Got 429 error. Backing off for {new_backoff} seconds until {self.backoff_until}")
        
        return new_backoff
    
    def wait_if_needed(self):
        """Wait if necessary before making a request (with shutdown support)"""
        while not self.can_make_request():
            # Check for shutdown signal
            if self._shutdown.is_set():
                logger.info("Rate limiter shutting down, stopping wait")
                raise KeyboardInterrupt("Shutdown requested")
            
            now = datetime.now(timezone.utc)
            
            if self.backoff_until and now < self.backoff_until:
                wait_seconds = (self.backoff_until - now).total_seconds()
                print(f"⏳ Rate limited. Waiting {wait_seconds:.0f} seconds...")
                print(f"   (Press Ctrl+C to force shutdown)")
                
                # Wait in small chunks so we can check for shutdown
                wait_time = min(wait_seconds, 5)  # Check every 5 seconds
                self._shutdown.wait(wait_time)
                
                if self._shutdown.is_set():
                    logger.info("Shutdown during rate limit wait")
                    raise KeyboardInterrupt("Shutdown requested")
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
                        print(f"   (Press Ctrl+C to force shutdown)")
                        
                        # Wait in small chunks
                        wait_time = min(wait_seconds + 1, 5)
                        self._shutdown.wait(wait_time)
                        
                        if self._shutdown.is_set():
                            logger.info("Shutdown during rate limit wait")
                            raise KeyboardInterrupt("Shutdown requested")
                else:
                    break
    
    def reset(self):
        """Reset the rate limiter"""
        self.requests_made = []
        self.backoff_until = None
        self.last_429_time = None
        self._shutdown.clear()

# Global rate limiter instance
rate_limiter = None

def get_rate_limiter():
    """Get the global rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = ImprovedRateLimiter()
    return rate_limiter

def shutdown_rate_limiter():
    """Shutdown the rate limiter gracefully"""
    global rate_limiter
    if rate_limiter:
        rate_limiter.shutdown()