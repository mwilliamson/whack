class Installer(object):
    def __init__(self, package_source_fetcher, package_provider, deployer):
        self._package_source_fetcher = package_source_fetcher
        self._package_provider = package_provider
        self._deployer = deployer

    def install(self, package_name, install_dir, params=None):
        self.get_package(package_name, install_dir, params)
        self._deployer.deploy(install_dir)
    
    def get_package(self, package_name, target_dir, params=None):
        if params is None:
            params = {}
            
        with self._fetch_package_source(package_name) as package_source:    
            self._provide_package(package_source, params, target_dir)
        
    def _provide_package(self, package_source, params, install_dir):
        return self._package_provider.provide_package(
            package_source,
            params,
            install_dir
        )
            
    def _fetch_package_source(self, package_name):
        return self._package_source_fetcher.fetch(package_name)
