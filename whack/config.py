import collections

def caching_config(enabled, http_cache_url=None):
    return CachingConfig(enabled=enabled, http_cache_url=http_cache_url)

CachingConfig = collections.namedtuple(
    "CachingConfig",
    ["enabled", "http_cache_url"]
)
