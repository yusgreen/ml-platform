"""Tiny in-memory TTL cache for chat responses."""

import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple

_lock = threading.Lock()
_cache: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()


def get(key: str) -> Optional[Any]:
    now = time.time()
    with _lock:
        item = _cache.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < now:
            _cache.pop(key, None)
            return None
        _cache.move_to_end(key)
        return value


def set(key: str, value: Any, ttl_seconds: int = 600, max_size: int = 200) -> None:
    now = time.time()
    with _lock:
        _cache[key] = (now + ttl_seconds, value)
        _cache.move_to_end(key)
        while len(_cache) > max_size:
            _cache.popitem(last=False)


def clear() -> None:
    with _lock:
        _cache.clear()
