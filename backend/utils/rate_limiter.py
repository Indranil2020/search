"""
Rate Limiter

Token bucket algorithm for API rate limiting.
"""

import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    
    capacity: float
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float
    
    def __init__(self, requests_per_second: float):
        self.capacity = requests_per_second
        self.tokens = requests_per_second
        self.refill_rate = requests_per_second
        self.last_refill = time.time()
    
    def refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def take(self) -> float:
        """Take a token, return wait time if needed."""
        self.refill()
        
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return 0.0
        
        # Calculate wait time
        wait_time = (1.0 - self.tokens) / self.refill_rate
        return wait_time


class RateLimiter:
    """Rate limiter using token bucket."""
    
    def __init__(self, requests_per_second: float = 10.0):
        self.bucket = TokenBucket(requests_per_second)
    
    def wait(self) -> None:
        """Wait if needed to respect rate limit."""
        wait_time = self.bucket.take()
        if wait_time > 0:
            time.sleep(wait_time)


class MultiRateLimiter:
    """Rate limiter for multiple sources."""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
    
    def get_limiter(self, source: str, rate: float = 10.0) -> RateLimiter:
        """Get or create rate limiter for source."""
        if source not in self.limiters:
            self.limiters[source] = RateLimiter(rate)
        return self.limiters[source]
    
    def wait(self, source: str) -> None:
        """Wait for specific source rate limit."""
        limiter = self.limiters.get(source)
        if limiter:
            limiter.wait()
