import os

from catchy import HttpCacher, DirectoryCacher, NoCachingStrategy
import whack.builder

def install(package, install_dir, caching, builder_uris, params):
    if not caching.enabled:
        cacher = NoCachingStrategy()
    elif caching.http_cache_url is not None:
        # TODO: add DirectoryCacher in front of HttpCacher
        cacher = HttpCacher(caching.http_cache_url, caching.http_cache_key)
    else:
        cacher = DirectoryCacher(os.path.expanduser("~/.cache/whack/builds"))
            
    builder = whack.builder.Builders(cacher, builder_uris)
    builder.install(package, install_dir, params)

