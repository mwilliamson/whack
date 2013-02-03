from .deployer import PackageDeployer
from .sources import PackageSourceFetcher


class Installer(object):
    def __init__(self, package_provider, package_source_repo_uris=None):
        if package_source_repo_uris is None:
            package_source_repo_uris = []
            
        self._package_provider = package_provider
        self._package_source_fetcher = PackageSourceFetcher(package_source_repo_uris)
        self._deployer = PackageDeployer()

    def install(self, package_name, install_dir, params=None):
        with self._fetch_package_source(package_name) as package_source:
            return self.install_from_package_source(package_source, install_dir, params)
            
    def install_from_package_source(self, package_source, install_dir, params=None):
        if params is None:
            params = {}
            
        with self._provide_package(package_source, params) as package_dir:
            self._deployer.deploy(package_source, package_dir, install_dir)
            
    def _provide_package(self, package_source, params):
        return self._package_provider.provide_package(package_source, params)
            
    def _fetch_package_source(self, package_name):
        return self._package_source_fetcher.fetch(package_name)
