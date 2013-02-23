import os
import subprocess

from . import downloads
from .tempdir import create_temporary_dir
from .naming import name_package
from .common import WHACK_ROOT, PackageNotAvailableError
from .files import mkdir_p


def create_package_provider(cacher, enable_build=True):
    underlying_providers = []
    if enable_build:
        underlying_providers.append(BuildingPackageProvider())
    return CachingPackageProvider(cacher, underlying_providers)


class BuildingPackageProvider(object):
    def provide_package(self, package_src, params, package_dir):
        with create_temporary_dir() as build_dir:
            self._build(package_src, build_dir, package_dir, params)
        return True
    
    def _build(self, package_src, build_dir, package_dir, params):
        package_src.write_to(build_dir)
            
        build_env = params_to_build_env(params)
        self._fetch_downloads(build_dir, build_env)
            
        build_script = os.path.join(build_dir, "whack/build")
        mkdir_p(package_dir)
        build_command = [
            "whack-run",
            os.path.abspath(package_dir), # package_dir is mounted at WHACK_ROOT
            build_script, # build_script is executed
            WHACK_ROOT # WHACK_ROOT is passed as the first argument to build_script
        ]
        subprocess.check_call(build_command, cwd=build_dir, env=build_env)

    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        downloads.fetch_downloads(downloads_file_path, build_env, build_dir)


class CachingPackageProvider(object):
    def __init__(self, cacher, underlying_providers):
        self._cacher = cacher
        self._underlying_providers = underlying_providers
    
    def provide_package(self, package_source, params, package_dir):
        package_name = name_package(package_source, params)
        result = self._cacher.fetch(package_name, package_dir)
        
        if not result.cache_hit:
            self._provide_package_without_cache(package_source, params, package_dir)
            self._cacher.put(package_name, package_dir)
            
    def _provide_package_without_cache(self, package_source, params, package_dir):
        for underlying_provider in self._underlying_providers:
            package = underlying_provider.provide_package(package_source, params, package_dir)
            if package is not None:
                return package
        raise PackageNotAvailableError()
        


def params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env
