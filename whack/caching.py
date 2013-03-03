import os

from catchy import xdg_directory_cacher, NoCachingStrategy


def create_cacher_factory(caching_enabled):
    if not caching_enabled:
        return NoCacheCachingFactory()
    else:
        return LocalCachingFactory()


class NoCacheCachingFactory(object):
    def create(self, name):
        return NoCachingStrategy()
        

class LocalCachingFactory(object):
    def create(self, name):
        return xdg_directory_cacher(os.path.join("whack", name))
