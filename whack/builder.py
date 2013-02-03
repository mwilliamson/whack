from .installer import PackageDeployer
from .providers import CachingPackageProvider
from .sources import PackageSourceFetcher


class Builders(object):
    def __init__(self, cacher, package_source_repo_uris):
        self._cacher = cacher
        self._package_source_fetcher = PackageSourceFetcher(package_source_repo_uris)

    def install(self, package_name, install_dir, params=None):
        with self._fetch_package(package_name) as package_source:
            deployer = PackageDeployer(CachingPackageProvider(self._cacher))
            return deployer.deploy(package_source, install_dir, params=params)
            
    def _fetch_package(self, package_name):
        return self._package_source_fetcher.fetch(package_name)
