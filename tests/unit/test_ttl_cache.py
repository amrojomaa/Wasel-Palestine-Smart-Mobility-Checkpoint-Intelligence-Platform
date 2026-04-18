import time

from app.utils.ttl_cache import TTLCache


def test_ttl_cache_set_get_hit():
    cache = TTLCache()
    cache.set("k1", {"value": 1}, ttl_seconds=2)
    assert cache.get("k1") == {"value": 1}


def test_ttl_cache_expiry():
    cache = TTLCache()
    cache.set("k2", "x", ttl_seconds=1)
    time.sleep(1.1)
    assert cache.get("k2") is None
