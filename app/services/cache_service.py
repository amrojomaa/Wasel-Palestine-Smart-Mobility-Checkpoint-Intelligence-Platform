from app.utils.ttl_cache import TTLCache


class CacheService:
    _cache = TTLCache()

    @classmethod
    def get(cls, key: str):
        return cls._cache.get(key)

    @classmethod
    def set(cls, key: str, value, ttl_seconds: int) -> None:
        cls._cache.set(key, value, ttl_seconds)
