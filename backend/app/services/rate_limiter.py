"""Simple in-memory rate limiter (sliding window)."""

import threading
import time
from typing import Dict, List

_lock = threading.Lock()
_hits: Dict[str, List[float]] = {}


def check_rate_limit(key: str, max_requests: int = 20, window_seconds: int = 60) -> bool:
    """Return True if the request is allowed, False if the limit is exceeded."""
    now = time.time()
    cutoff = now - window_seconds
    with _lock:
        timestamps = _hits.get(key, [])
        timestamps = [t for t in timestamps if t > cutoff]
        if len(timestamps) >= max_requests:
            _hits[key] = timestamps
            return False
        timestamps.append(now)
        _hits[key] = timestamps
        return True


def reset(key: str | None = None) -> None:
    with _lock:
        if key is None:
            _hits.clear()
        else:
            _hits.pop(key, None)
