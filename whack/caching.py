import os
import tempfile
import shutil

class DirectoryCacher(object):
    def __init__(self, cacher_dir):
        self._cacher_dir = cacher_dir
    
    def fetch(self, install_id, build_dir):
        if self._in_cache(install_id):
            shutil.copytree(self._cache_dir(install_id), build_dir)
            return CacheHit()
        else:
            return CacheMiss()
            
    def put(self, install_id, build_dir):
        # TODO: locking
        if not self._in_cache(install_id):
            shutil.copytree(build_dir, self._cache_dir(install_id))
            open(self._cache_indicator(install_id), "w").write("")
    
    def _in_cache(self, install_id):
        return os.path.exists(self._cache_indicator(install_id))
    
    def _cache_dir(self, install_id):
        return os.path.join(self._cacher_dir, install_id)
        
    def _cache_indicator(self, install_id):
        return os.path.join(self._cacher_dir, "{0}.built".format(install_id))


# TODO: eurgh, what a horrible name
class NoCachingStrategy(object):
    def fetch(self, install_id, build_dir):
        return CacheMiss()
    
    def put(self, install_id, build_dir):
        pass


class CacheHit(object):
    cache_hit = True

    
class CacheMiss(object):
    cache_hit = False
