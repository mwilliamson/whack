import os

from whack.caching import DirectoryCacher, NoCachingStrategy
import whack.builder

def install(package, install_dir, should_cache, http_cache, builder_uris, params):
    if should_cache:
        cacher = DirectoryCacher(os.path.expanduser("~/.cache/whack/builds"))
    else:
        cacher = NoCachingStrategy()
            
    builder = whack.builder.Builders(cacher, builder_uris)
    builder.install(package, install_dir, params)
