import os
import subprocess
import shutil
import json
import uuid
import stat
import contextlib

import spur

from . import downloads
from . import templates
from .hashes import Hasher
from .tempdir import create_temporary_dir


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
        
        def run(command):
            subprocess.check_call(
                command,
                cwd=build_dir,
                env=build_env
            )
        template = templates.template(package_src.template_name())
        template.build(run, build_dir, package_dir)

    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        downloads_file = self._read_downloads_file(downloads_file_path, build_env)
        for download_line in downloads_file:
            downloads.download(download_line.url, os.path.join(build_dir, download_line.filename))

    def _read_downloads_file(self, path, build_env):
        if os.path.exists(path):
            first_line = open(path).readline()
            if first_line.startswith("#!"):
                downloads_string = subprocess.check_output(
                    [path],
                    env=build_env
                )
            else:
                downloads_string = open(path).read()
                
            return downloads.read_downloads_string(downloads_string)
        else:
            return []


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
