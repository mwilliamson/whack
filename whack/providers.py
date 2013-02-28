from .naming import generate_package_hash
from .common import PackageNotAvailableError
from .builder import build
from .tarballs import extract_tarball
from .indices import read_index


def create_package_provider(cacher, enable_build=True, indices=None):
    if indices is None:
        indices = []
    
    underlying_providers = map(IndexPackageProvider, indices)
    if enable_build:
        underlying_providers.append(BuildingPackageProvider())
    return CachingPackageProvider(cacher, underlying_providers)


class IndexPackageProvider(object):
    def __init__(self, index_uri):
        self._index_uri = index_uri
        
    def provide_package(self, package_source, params, package_dir):
        # TODO: bundle up package_source and params into a PackageRequest
        package_hash = generate_package_hash(package_source, params)
        index = read_index(self._index_uri)
        package_entry = index.find_package_by_hash(package_hash)
        if package_entry is None:
            return None
        else:
            self._fetch_and_extract(package_entry.url, package_dir)
            return True
        
    def _fetch_and_extract(self, url, package_dir):
        extract_tarball(url, package_dir, strip_components=1)
        

class BuildingPackageProvider(object):
    def provide_package(self, package_src, params, package_dir):
        build(package_src, params, package_dir)
        return True


class CachingPackageProvider(object):
    def __init__(self, cacher, underlying_providers):
        self._cacher = cacher
        self._underlying_providers = underlying_providers
    
    def provide_package(self, package_source, params, package_dir):
        package_hash = generate_package_hash(package_source, params)
        result = self._cacher.fetch(package_hash, package_dir)
        
        if not result.cache_hit:
            self._provide_package_without_cache(package_source, params, package_dir)
            self._cacher.put(package_hash, package_dir)
            
    def _provide_package_without_cache(self, package_source, params, package_dir):
        for underlying_provider in self._underlying_providers:
            package = underlying_provider.provide_package(package_source, params, package_dir)
            if package is not None:
                return package
        raise PackageNotAvailableError()
