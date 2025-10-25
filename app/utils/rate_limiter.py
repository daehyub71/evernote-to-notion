"""
Rate Limiter for API calls.

Prevents exceeding API rate limits by throttling requests.
"""

import time
from threading import Lock
from typing import Optional


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.

    Ensures API calls don't exceed specified rate limits.
    """

    def __init__(self, calls_per_second: float = 3.0, burst: Optional[int] = None):
        """
        Initialize rate limiter.

        Args:
            calls_per_second: Maximum number of calls per second
            burst: Maximum burst size (default: calls_per_second)
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.burst = burst if burst is not None else int(calls_per_second)

        self.tokens = float(self.burst)  # Available tokens
        self.last_update = time.time()
        self.lock = Lock()

    def wait(self, tokens: int = 1) -> float:
        """
        Wait until rate limit allows the request.

        Args:
            tokens: Number of tokens to consume (default: 1)

        Returns:
            Time waited in seconds
        """
        with self.lock:
            start_time = time.time()

            # Refill tokens based on elapsed time
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.calls_per_second)
            self.last_update = now

            # Wait if not enough tokens
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.calls_per_second
                time.sleep(wait_time)

                # Update after waiting
                self.tokens = 0
                self.last_update = time.time()
            else:
                self.tokens -= tokens

            return time.time() - start_time

    def __enter__(self):
        """Context manager entry."""
        self.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class NotionRateLimiter(RateLimiter):
    """
    Rate limiter specifically for Notion API.

    Notion API limits:
    - 3 requests per second per integration
    - Burst tolerance: ~10 requests
    """

    def __init__(self):
        """Initialize with Notion-specific limits."""
        super().__init__(calls_per_second=3.0, burst=10)
