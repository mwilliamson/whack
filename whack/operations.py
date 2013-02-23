from catchy import xdg_directory_cacher, NoCachingStrategy

from .installer import Installer
from .sources import PackageSourceFetcher, create_source_tarball
from .providers import CachingPackageProvider
from .deployer import PackageDeployer


def create(caching_enabled):
    if not caching_enabled:
        cacher = NoCachingStrategy()
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
        
    def deploy(self, package_dir, target_dir=None):
        return self._deployer.deploy(package_dir, target_dir)
        
    def create_source_tarball(self, source_dir, tarball_dir):
        return create_source_tarball(source_dir, tarball_dir)
