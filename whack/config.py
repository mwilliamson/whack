import collections

def caching_config(**kwargs):
    updated_kwargs = {"http_cache_url": None, "http_cache_key": None}
    updated_kwargs.update(kwargs)
    return CachingConfig(**updated_kwargs)

CachingConfig = collections.namedtuple(
    "CachingConfig",
    ["enabled", "http_cache_url", "http_cache_key"]
)
