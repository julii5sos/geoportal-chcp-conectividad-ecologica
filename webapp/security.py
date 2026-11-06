"""Controles de abuso y concurrencia para la API web.

La autenticación de usuarios corresponde a Cloud Run IAM. Estos controles son una
segunda barrera para errores de cliente y uso excesivo dentro de cada instancia.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int


class SlidingWindowRateLimiter:
    """Limitador acotado en memoria; no pretende sustituir cuotas perimetrales."""

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int,
        max_keys: int = 2048,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self.max_keys = max(16, int(max_keys))
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._last_seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, identity: str) -> RateLimitDecision:
        now = self._clock()
        cutoff = now - self.window_seconds
        key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - events[0])) + 1)
                return RateLimitDecision(False, self.limit, 0, retry_after)
            events.append(now)
            self._last_seen[key] = now
            if len(self._events) > self.max_keys:
                stale = sorted(self._last_seen, key=self._last_seen.get)[: len(self._events) - self.max_keys]
                for stale_key in stale:
                    self._events.pop(stale_key, None)
                    self._last_seen.pop(stale_key, None)
            return RateLimitDecision(True, self.limit, self.limit - len(events), 0)


class ConcurrencyGate:
    """Semáforo no bloqueante para no acumular cálculos científicos en memoria."""

    def __init__(self, maximum: int = 1):
        self.maximum = max(1, min(int(maximum), 4))
        self._semaphore = threading.BoundedSemaphore(self.maximum)

    def acquire(self) -> bool:
        return self._semaphore.acquire(blocking=False)

    def release(self) -> None:
        self._semaphore.release()

