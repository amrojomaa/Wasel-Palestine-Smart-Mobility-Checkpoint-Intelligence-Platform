import time
from collections import deque

from app.core.exceptions import RateLimitedException


class AbusePreventionService:
    # Process-local limiter state. This is intended for single-instance deployments.
    # In multi-replica environments, move buckets to a shared store (e.g. Redis).
    _by_user: dict[str, deque[float]] = {}
    _by_ip: dict[str, deque[float]] = {}

    MAX_PER_MINUTE_USER = 6
    MAX_PER_MINUTE_IP = 20
    COOLDOWN_SECONDS = 10

    @classmethod
    def check_report_submission(cls, user_id: str, ip_address: str | None) -> None:
        now = time.time()
        cls._check_bucket(cls._by_user, f"user:{user_id}", now, cls.MAX_PER_MINUTE_USER)

        if ip_address:
            cls._check_bucket(cls._by_ip, f"ip:{ip_address}", now, cls.MAX_PER_MINUTE_IP)

        user_bucket = cls._by_user.get(f"user:{user_id}")
        if user_bucket and len(user_bucket) >= 2 and (now - user_bucket[-2]) < cls.COOLDOWN_SECONDS:
            raise RateLimitedException(message="Cooldown active. Please wait before submitting another report.")

    @classmethod
    def _check_bucket(cls, storage: dict[str, deque[float]], key: str, now: float, max_per_minute: int) -> None:
        bucket = storage.setdefault(key, deque())
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= max_per_minute:
            raise RateLimitedException(message="Too many report submissions. Please slow down.")
        bucket.append(now)
