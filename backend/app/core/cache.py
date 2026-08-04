import time
from typing import Any, Optional

class TTLCache:
    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > time.time():
                return value
            else:
                self.delete(key)
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self._cache[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        self._cache.clear()

cache = TTLCache()
