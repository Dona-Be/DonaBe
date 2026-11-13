import threading
import time
from collections import Counter

from fastapi import HTTPException, status

from src.api.authentication import ProfileOwner

TOO_MANY_ATTEMPTS_MESSAGE = "Muitas tentativas. Tente novamente mais tarde."


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._lock = threading.Lock()
        self._attempts: Counter[str] = Counter()
        self._window_end = 0.0

    def count_attempt(self, key: str) -> bool:
        with self._lock:
            now = time.monotonic()
            # One window for every key, so the memory empties when it ends.
            if now >= self._window_end:
                self._attempts.clear()
                self._window_end = now + self._window_seconds
            self._attempts[key] += 1
            return self._attempts[key] <= self._max_attempts

    def reset(self) -> None:
        with self._lock:
            self._attempts.clear()


# Kept in memory, which is enough while the API runs as a single process.
CEP_LOOKUPS_PER_ACCOUNT = RateLimiter(max_attempts=20, window_seconds=60 * 60)


def limit_cep_lookups(owner: ProfileOwner) -> None:
    if not CEP_LOOKUPS_PER_ACCOUNT.count_attempt(owner.email):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, TOO_MANY_ATTEMPTS_MESSAGE)
