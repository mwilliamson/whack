import os

from whack.caching import DirectoryCacher, NoCachingStrategy
import whack.builder

def install(package, install_dir, caching, builder_uris, params):
    if caching.enabled:
        cacher = DirectoryCacher(os.path.expanduser("~/.cache/whack/builds"))
    else:
        cacher = NoCachingStrategy()
            
    builder = whack.builder.Builders(cacher, builder_uris)
    builder.install(package, install_dir, params)

