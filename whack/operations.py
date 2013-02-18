from catchy import HttpCacher, xdg_directory_cacher, NoCachingStrategy

from .installer import Installer
from .sources import PackageSourceFetcher
from .providers import CachingPackageProvider
from .deployer import PackageDeployer


def create(caching):
    if not caching.enabled:
        cacher = NoCachingStrategy()
    elif caching.http_cache_url is not None:
        # TODO: add DirectoryCacher in front of HttpCacher
        cacher = HttpCacher(caching.http_cache_url, caching.http_cache_key)
    else:
        cacher = xdg_directory_cacher("whack/builds")
    
    package_source_fetcher = PackageSourceFetcher()
    package_provider = CachingPackageProvider(cacher)
    deployer = PackageDeployer()
    installer = Installer(package_source_fetcher, package_provider, deployer)
    
    return Operations(installer, deployer)


class Operations(object):
    def __init__(self, installer, deployer):
        self._installer = installer
        self._deployer = deployer
        
    def install(self, package_name, install_dir, params):
        return self._installer.install(package_name, install_dir, params)
        
    def build(self, package_name, install_dir, params):
        return self._installer.build(package_name, install_dir, params)
        
    def deploy(self, package_dir):
        return self._deployer.deploy(package_dir)


def install(package, install_dir, caching, params):
    operations = create(caching)
    operations.install(package, install_dir, params)
    

def build(package, install_dir, caching, params):
    operations = create(caching)
    operations.build(package, install_dir, params)


def deploy(package_dir, caching):
    operations = create(caching)
    operations.deploy(package_dir)
