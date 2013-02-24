import os

from catchy import xdg_directory_cacher, NoCachingStrategy

from .installer import Installer
from .sources import PackageSourceFetcher, create_source_tarball
from .providers import create_package_provider
from .deployer import PackageDeployer
from .tempdir import create_temporary_dir
from .files import read_file
from .tarballs import create_tarball


def create(caching_enabled, indices=None, enable_build=True):
    if not caching_enabled:
        cacher = NoCachingStrategy()
    else:
        cacher = xdg_directory_cacher("whack/builds")
    
    package_source_fetcher = PackageSourceFetcher(indices)
    package_provider = create_package_provider(
        cacher,
        enable_build=enable_build,
        indices=indices,
    )
    deployer = PackageDeployer()
    installer = Installer(package_source_fetcher, package_provider, deployer)
    
    return Operations(installer, deployer)


class Operations(object):
    def __init__(self, installer, deployer):
        self._installer = installer
        self._deployer = deployer
        
    def install(self, package_name, install_dir, params=None):
        return self._installer.install(package_name, install_dir, params)
        
    def get_package(self, package_name, install_dir, params=None):
        return self._installer.get_package(package_name, install_dir, params)
        
    def deploy(self, package_dir, target_dir=None):
        return self._deployer.deploy(package_dir, target_dir)
        
    def create_source_tarball(self, source_dir, tarball_dir):
        return create_source_tarball(source_dir, tarball_dir)
        
    def build_package_tarball(self, package_name, tarball_dir, params=None):
        with create_temporary_dir() as package_dir:
            self.get_package(package_name, package_dir, params=params)
            package_name = read_file(os.path.join(package_dir, ".whack-package-name"))
            package_filename = "{0}.whack-package".format(package_name)
            package_tarball_path = os.path.join(tarball_dir, package_filename)
            create_tarball(package_tarball_path, package_dir, rename_dir=package_name)
            return PackageTarball(package_tarball_path)


class PackageTarball(object):
    def __init__(self, path):
        self.path = path
