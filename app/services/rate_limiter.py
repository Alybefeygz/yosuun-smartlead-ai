"""Small in-process sliding-window limiter for the public chat endpoint."""

from __future__ import annotations

from collections import deque
from math import ceil
from threading import Lock
from time import monotonic
from typing import Deque, Dict


class SlidingWindowRateLimiter:
    """Allow a bounded number of requests per client and time window."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        if max_requests <= 0 or window_seconds <= 0:
            raise ValueError("Rate limit değerleri pozitif olmalıdır.")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, Deque[float]] = {}
        self._lock = Lock()

    def acquire(self, client_key: str) -> int:
        """Record an allowed request or return the number of seconds to retry."""

        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            requests = self._requests.setdefault(client_key, deque())
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= self.max_requests:
                return max(1, ceil(requests[0] + self.window_seconds - now))
            requests.append(now)
            return 0
