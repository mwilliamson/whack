import os
import tempfile
import shutil

class DirectoryCacher(object):
    def __init__(self, cacher_dir):
        self._cacher_dir = cacher_dir
        
    def cache_for_install(self, install_id):
        return DirectoryCache(os.path.join(self._cacher_dir, install_id))
        

class DirectoryCache(object):
    def __init__(self, cache_dir):
        self._cache_dir = cache_dir
        self.build_dir = self._cache_dir

    def already_built(self):
        return os.path.exists(self._cache_dir)
        
    def __enter__(self):
        # TODO: lock
        return self
        
    def __exit__(self, *args):
        pass

# TODO: eurgh, what a horrible name
class NoCachingStrategy(object):
    def cache_for_install(self, install_id):
        return NoCache(os.path.join(tempfile.mkdtemp(), "build"))
        

class NoCache(object):
    def  __init__(self, build_dir):
        self.build_dir = build_dir
    
    def already_built(self):
        return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

