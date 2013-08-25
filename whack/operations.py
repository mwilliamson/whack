import os
import sys

import dodge

from .sources import PackageSourceFetcher, create_source_tarball
from .providers import create_package_provider
from .deployer import PackageDeployer
from .tempdir import create_temporary_dir
from .files import read_file
from .tarballs import create_tarball
from .packagerequests import create_package_request, PackageDescription
from .caching import create_cacher_factory
from .testing import TestResult
from .env import params_to_env
from . import local
from .errors import PackageNotAvailableError


def create(caching_enabled, indices=None, enable_build=True):
    cacher_factory = create_cacher_factory(caching_enabled=caching_enabled)
    
    package_source_fetcher = PackageSourceFetcher(indices)
    package_provider = create_package_provider(
        cacher_factory,
        enable_build=enable_build,
        indices=indices,
    )
    deployer = PackageDeployer()
    
    return Operations(package_source_fetcher, package_provider, deployer)


class Operations(object):
    def __init__(self, package_source_fetcher, package_provider, deployer):
        self._package_source_fetcher = package_source_fetcher
        self._package_provider = package_provider
        self._deployer = deployer
        
    def install(self, source_name, install_dir, params=None):
        self.get_package(source_name, install_dir, params)
        self.deploy(install_dir)
        
    def get_package(self, source_name, install_dir, params=None):
        with self._package_source_fetcher.fetch(source_name) as package_source:
            request = create_package_request(package_source, params)
            if not self._package_provider.provide_package(request, install_dir):
                raise PackageNotAvailableError()
        
    def deploy(self, package_dir, target_dir=None):
        return self._deployer.deploy(package_dir, target_dir)
        
    def create_source_tarball(self, source_name, tarball_dir):
        with self._package_source_fetcher.fetch(source_name) as package_source:
            return create_source_tarball(package_source, tarball_dir)
        
    def get_package_tarball(self, package_name, tarball_dir, params=None):
        with create_temporary_dir() as package_dir:
            self.get_package(package_name, package_dir, params=params)
            package_description = dodge.loads(
                read_file(os.path.join(package_dir, ".whack-package.json")),
                PackageDescription
            )
            package_name = package_description.name
            package_filename = "{0}.whack-package".format(package_name)
            package_tarball_path = os.path.join(tarball_dir, package_filename)
            create_tarball(package_tarball_path, package_dir, rename_dir=package_name)
            return PackageTarball(package_tarball_path)
            
    def test(self, source_name, params=None):
        with self._package_source_fetcher.fetch(source_name) as package_source:
            description = package_source.description()
            test_command = description.test_command()
            if test_command is None:
                return TestResult(passed=False)
            else:
                return_code = local.run(
                    ["sh", "-c", test_command],
                    cwd=package_source.path,
                    update_env=params_to_env(params),
                    allow_error=True,
                    stdout=sys.stderr,
                    stderr=sys.stderr,
                ).return_code
                passed = return_code == 0
                return TestResult(passed=passed)


class PackageTarball(object):
    def __init__(self, path):
        self.path = path
