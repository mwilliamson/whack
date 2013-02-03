from .installer import PackageInstaller
from .sources import PackageSourceFetcher


class Builders(object):
    def __init__(self, cacher, package_source_repo_uris):
        self._cacher = cacher
        self._package_source_fetcher = PackageSourceFetcher(package_source_repo_uris)

    def install(self, package_name, install_dir, params=None):
        with self._fetch_package(package_name) as package_src_dir:
            builder = PackageInstaller(package_src_dir, self._cacher)
            return builder.install(install_dir, params=params)
            
    def _fetch_package(self, package_name):
        return self._package_source_fetcher.fetch(package_name)
