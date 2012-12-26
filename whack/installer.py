import os
import subprocess
import shutil
import json

from whack import downloads
from whack.hashes import Hasher
from whack.tempdir import create_temporary_dir

__all__ = ["PackageInstaller"]

class PackageInstaller(object):
    def __init__(self, package_dir, cacher):
        self._package_dir = package_dir
        self._cacher = cacher
    
    def install(self, install_dir, params={}):
        install_id = self._generate_install_id(params)
        
        with create_temporary_dir() as temp_dir:
            build_dir = os.path.join(temp_dir, "build")
            result = self._cacher.fetch(install_id, build_dir)
            if not result.cache_hit:
                self._build(build_dir, params)
                self._cacher.put(install_id, build_dir)
                
            self._run_install_script(build_dir, install_dir)

    def _build(self, build_dir, params):
        ignore = shutil.ignore_patterns(".svn", ".hg", ".hgignore", ".git", ".gitignore")
        shutil.copytree(self._package_dir, build_dir, ignore=ignore)
        build_env = params_to_build_env(params)
        
        self._fetch_downloads(build_dir, build_env)
        subprocess.check_call(
            [os.path.join(self._package_dir, "whack/build")],
            cwd=build_dir,
            env=build_env
        )

    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        downloads_file = self._read_downloads_file(downloads_file_path, build_env)
        for download_line in downloads_file:
            downloads.download(download_line.url, os.path.join(build_dir, download_line.filename))

    def _run_install_script(self, build_dir, install_dir):
        subprocess.check_call(
            [os.path.join(build_dir, "whack/install"), install_dir],
            cwd=build_dir
        )

    def _generate_install_id(self, params):
        hasher = Hasher()
        hasher.update(self._uname("--kernel-name"))
        hasher.update(self._uname("--machine"))
        hasher.update_with_dir(self._package_dir)
        hasher.update(json.dumps(params, sort_keys=True))
        return hasher.hexdigest()

    def _uname(self, arg):
        return subprocess.check_output(["uname", arg])

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

def params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env

