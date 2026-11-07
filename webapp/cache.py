"""Caché acotada para resultados científicos generados por la API."""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CachedResult:
    identifier: str
    signature: str
    created_at: float
    value: dict[str, Any]


class ResultCache:
    def __init__(self, *, max_entries: int = 8, ttl_seconds: int = 1800):
        self.max_entries = max(1, int(max_entries))
        self.ttl_seconds = max(60, int(ttl_seconds))
        self._by_id: OrderedDict[str, CachedResult] = OrderedDict()
        self._by_signature: dict[str, str] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._latest_by_territory: dict[str, str] = {}
        self._guard = threading.RLock()

    @staticmethod
    def signature(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _purge(self) -> None:
        now = time.time()
        expired = [
            identifier
            for identifier, item in self._by_id.items()
            if now - item.created_at > self.ttl_seconds
        ]
        for identifier in expired:
            item = self._by_id.pop(identifier)
            self._by_signature.pop(item.signature, None)
            self._latest_by_territory = {
                key: value for key, value in self._latest_by_territory.items()
                if value != identifier
            }
        while len(self._by_id) > self.max_entries:
            identifier, item = self._by_id.popitem(last=False)
            self._by_signature.pop(item.signature, None)
            self._latest_by_territory = {
                key: value for key, value in self._latest_by_territory.items()
                if value != identifier
            }

    def get(self, identifier: str) -> CachedResult | None:
        with self._guard:
            self._purge()
            item = self._by_id.get(identifier)
            if item:
                self._by_id.move_to_end(identifier)
            return item

    def latest(self, territory_key: str) -> CachedResult | None:
        with self._guard:
            self._purge()
            identifier = self._latest_by_territory.get(territory_key)
            return self.get(identifier) if identifier else None

    def run_once(
        self,
        payload: dict[str, Any],
        operation: Callable[[], dict[str, Any]],
        *,
        territory_key: str | None = None,
    ) -> tuple[CachedResult, bool]:
        signature = self.signature(payload)
        with self._guard:
            self._purge()
            existing_id = self._by_signature.get(signature)
            if existing_id and existing_id in self._by_id:
                item = self._by_id[existing_id]
                self._by_id.move_to_end(existing_id)
                if territory_key:
                    self._latest_by_territory[territory_key] = item.identifier
                return item, True
            lock = self._locks.setdefault(signature, threading.Lock())

        try:
            with lock:
                with self._guard:
                    self._purge()
                    existing_id = self._by_signature.get(signature)
                    if existing_id and existing_id in self._by_id:
                        item = self._by_id[existing_id]
                        self._by_id.move_to_end(existing_id)
                        if territory_key:
                            self._latest_by_territory[territory_key] = item.identifier
                        return item, True
                value = operation()
                item = CachedResult(
                    identifier=uuid.uuid4().hex,
                    signature=signature,
                    created_at=time.time(),
                    value=value,
                )
                with self._guard:
                    self._by_id[item.identifier] = item
                    self._by_signature[signature] = item.identifier
                    if territory_key:
                        self._latest_by_territory[territory_key] = item.identifier
                    self._purge()
                return item, False
        finally:
            with self._guard:
                if self._locks.get(signature) is lock:
                    self._locks.pop(signature, None)

