import os
import subprocess
import shutil
import contextlib

from . import downloads
from .tempdir import create_temporary_dir
from .naming import name_package
from .common import WHACK_ROOT


class BuildingPackageProvider(object):
    @contextlib.contextmanager
    def provide_package(self, package_src, params):
        with create_temporary_dir() as temp_dir:
            build_dir = os.path.join(temp_dir, "build")
            package_dir = os.path.join(temp_dir, "package")
            
            self._build(package_src, build_dir, package_dir, params)
                
            yield package_dir
    
    def _build(self, package_src, build_dir, package_dir, params):
        ignore = shutil.ignore_patterns(".svn", ".hg", ".hgignore", ".git", ".gitignore")
        shutil.copytree(package_src.path, build_dir, ignore=ignore)
        build_env = params_to_build_env(params)
        self._fetch_downloads(build_dir, build_env)
            
        build_script = os.path.join(build_dir, "whack/build")
        os.mkdir(package_dir)
        build_command = [
            "whack-run-with-whack-root",
            package_dir, # package_dir is mounted at WHACK_ROOT
            build_script, # build_script is executed
            WHACK_ROOT # WHACK_ROOT is passed as the first argument to build_script
        ]
        subprocess.check_call(build_command, cwd=build_dir, env=build_env)

    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        downloads.fetch_downloads(downloads_file_path, build_env, build_dir)


class CachingPackageProvider(object):
    def __init__(self, cacher):
        self._cacher = cacher
        self._underlying_provider = BuildingPackageProvider()
    
    @contextlib.contextmanager
    def provide_package(self, package_source, params):
        package_name = name_package(package_source, params)
        
        with create_temporary_dir() as temp_dir:
            cached_package_dir = os.path.join(temp_dir, "package")
            
            result = self._cacher.fetch(package_name, cached_package_dir)
            
            if result.cache_hit:
                yield cached_package_dir
            else:
                with self._underlying_provider.provide_package(package_source, params) as package_dir:
                    self._cacher.put(package_name, package_dir)
                    yield package_dir


def params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env
