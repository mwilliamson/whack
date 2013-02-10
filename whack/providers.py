import os
import subprocess
import shutil
import json
import contextlib
import stat

from . import downloads
from .hashes import Hasher
from .tempdir import create_temporary_dir
from .executables import create_directly_executable_dir
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
            package_dir,
            build_script,
            WHACK_ROOT
        ]
        subprocess.check_call(build_command, cwd=build_dir, env=build_env)
                
        with open(os.path.join(package_dir, "run"), "w") as run_file:
            run_file.write('#!/usr/bin/env sh\nexec whack-run-with-whack-root "$(dirname $0)" "$@"')
        subprocess.check_call(["chmod", "+x", os.path.join(package_dir, "run")])
        
        create_directly_executable_dir(package_dir, "bin")
        create_directly_executable_dir(package_dir, "sbin")

    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        downloads.fetch_downloads(downloads_file_path, build_env, build_dir)


class CachingPackageProvider(object):
    def __init__(self, cacher):
        self._cacher = cacher
        self._underlying_provider = BuildingPackageProvider()
    
    @contextlib.contextmanager
    def provide_package(self, package_source, params):
        install_id = _generate_install_id(package_source.path, params)
        
        with create_temporary_dir() as temp_dir:
            cached_package_dir = os.path.join(temp_dir, "package")
            
            result = self._cacher.fetch(install_id, cached_package_dir)
            
            if result.cache_hit:
                yield cached_package_dir
            else:
                with self._underlying_provider.provide_package(package_source, params) as package_dir:
                    self._cacher.put(install_id, package_dir)
                    yield package_dir


def params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env
    

def _generate_install_id(package_src_dir, params):
    hasher = Hasher()
    hasher.update(_uname("--kernel-name"))
    hasher.update(_uname("--machine"))
    hasher.update_with_dir(package_src_dir)
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.hexdigest()


def _uname(arg):
    return subprocess.check_output(["uname", arg])
