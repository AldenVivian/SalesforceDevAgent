# context/tool_cache.py
import time
import os
import json
from typing import Any, Optional


class TTLCache:
    def __init__(self, default_ttl: int = 300):
        self._store = {}
        self._ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        value, exp = item
        if time.time() > exp:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self._store[key] = (value, time.time() + (ttl or self._ttl))


cache = TTLCache(default_ttl=int(os.getenv("CACHE_TTL_SECONDS", "300")))
