import os

from catchy import HttpCacher, DirectoryCacher, NoCachingStrategy

from .installer import Installer
from .sources import PackageSourceFetcher
from .providers import CachingPackageProvider
from .deployer import PackageDeployer


def install(*args, **kwargs):
    return _installer_command(lambda installer: installer.install, *args, **kwargs)
    

def build(*args, **kwargs):
    return _installer_command(lambda installer: installer.build, *args, **kwargs)


def _installer_command(command, package, install_dir, caching, params):
    if not caching.enabled:
        cacher = NoCachingStrategy()
    elif caching.http_cache_url is not None:
        # TODO: add DirectoryCacher in front of HttpCacher
        cacher = HttpCacher(caching.http_cache_url, caching.http_cache_key)
    else:
        cacher = DirectoryCacher(os.path.expanduser("~/.cache/whack/builds"))
    
    package_source_fetcher = PackageSourceFetcher()
    package_provider = CachingPackageProvider(cacher)
    deployer = PackageDeployer()
    installer = Installer(package_source_fetcher, package_provider, deployer)
    command(installer)(package, install_dir, params)
    
