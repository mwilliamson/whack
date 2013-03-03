from .errors import PackageNotAvailableError
from .builder import Builder
from .tarballs import extract_tarball
from .indices import read_index
from .downloads import Downloader


def create_package_provider(cacher_factory, enable_build=True, indices=None):
    if indices is None:
        indices = []
    
    underlying_providers = map(IndexPackageProvider, indices)
    if enable_build:
        downloader = Downloader(cacher_factory.create("downloads"))
        underlying_providers.append(BuildingPackageProvider(Builder(downloader)))
    return CachingPackageProvider(
        cacher_factory.create("packages"),
        underlying_providers
    )


class IndexPackageProvider(object):
    def __init__(self, index_uri):
        self._index_uri = index_uri
        
    def provide_package(self, package_request, package_dir):
        package_name = package_request.name()
        index = read_index(self._index_uri)
        package_entry = index.find_by_name("{0}.whack-package".format(package_name))
        if package_entry is None:
            return None
        else:
            self._fetch_and_extract(package_entry.url, package_dir)
            return True
        
    def _fetch_and_extract(self, url, package_dir):
        extract_tarball(url, package_dir, strip_components=1)
        

class BuildingPackageProvider(object):
    def __init__(self, builder):
        self._builder = builder
    
    def provide_package(self, package_request, package_dir):
        self._builder.build(package_request, package_dir)
        return True


class CachingPackageProvider(object):
    def __init__(self, cacher, underlying_providers):
        self._cacher = cacher
        self._underlying_providers = underlying_providers
    
    def provide_package(self, package_request, package_dir):
        package_name = package_request.name()
        result = self._cacher.fetch(package_name, package_dir)
        
        if not result.cache_hit:
            self._provide_package_without_cache(package_request, package_dir)
            self._cacher.put(package_name, package_dir)
            
    def _provide_package_without_cache(self, package_request, package_dir):
        for underlying_provider in self._underlying_providers:
            package = underlying_provider.provide_package(package_request, package_dir)
            if package is not None:
                return package
        
        raise PackageNotAvailableError()
