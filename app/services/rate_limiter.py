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
            self._prune_expired_clients(cutoff)
            requests = self._requests.setdefault(client_key, deque())
            if len(requests) >= self.max_requests:
                return max(1, ceil(requests[0] + self.window_seconds - now))
            requests.append(now)
            return 0

    def _prune_expired_clients(self, cutoff: float) -> None:
        """Drop expired timestamps and forget clients with none left.

        Visitor IDs are unbounded, so idle clients must not stay in memory.
        """

        for client_key in list(self._requests):
            requests = self._requests[client_key]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if not requests:
                del self._requests[client_key]
