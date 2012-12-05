import os
import subprocess
import shutil
import contextlib
import tempfile
import json

from whack import downloads
from whack.hashes import Hasher

class PackageInstaller(object):
    def __init__(self, package_dir, should_cache=True):
        self._package_dir = package_dir
        self._should_cache = should_cache
    
    def install(self, install_dir, params={}):
        install_id = self._generate_install_id(params)
        cacher = _create_cacher(self._should_cache)
        with cacher.cache_for_install(install_id) as cache:
            build_dir = cache.build_dir
            if not cache.already_built():
                self._build(build_dir, params)
            
            self._run_install_script(build_dir, install_dir)

    def _build(self, build_dir, params):
        try:
            ignore = shutil.ignore_patterns(".svn", ".hg", ".hgignore", ".git", ".gitignore")
            shutil.copytree(self._package_dir, build_dir, ignore=ignore)
            self._fetch_downloads(build_dir)
            
            build_env = os.environ.copy()
            for name, value in params.iteritems():
                build_env[name] = str(value)
            subprocess.check_call(
                [os.path.join(self._package_dir, "build")],
                cwd=build_dir,
                env=build_env
            )
        except:
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
            raise

    def _fetch_downloads(self, build_dir):
        downloads_file_path = os.path.join(build_dir, "downloads")
        download_urls = self._read_downloads_file(downloads_file_path)
        for url in download_urls:
            downloads.download_to_dir(url, build_dir)

    def _run_install_script(self, build_dir, install_dir):
        subprocess.check_call(
            [os.path.join(build_dir, "install"), install_dir],
            cwd=build_dir
        )

    def _generate_install_id(self, params):
        hasher = Hasher()
        hasher.update_with_dir(self._package_dir)
        hasher.update(json.dumps(params))
        return hasher.hexdigest()

    def _read_downloads_file(self, path):
        if os.path.exists(path):
            first_line = open(path).readline()
            if first_line.startswith("#!"):
                downloads_output = subprocess.check_output(
                    [path],
                    env={"VERSION": self._package_version}
                )
                lines = downloads_output.split("\n")
            else:
                lines = open(path)
                
            return [line.strip() for line in lines if line]
        else:
            return []

def _create_cacher(should_cache):
    if should_cache:
        return DirectoryCacher(os.path.expanduser("~/.cache/whack/builds"))
    else:
        return NoCachingStrategy()

class DirectoryCacher(object):
    def __init__(self, cacher_dir):
        self._cacher_dir = cacher_dir
        
    def cache_for_install(self, install_id):
        return DirectoryCache(os.path.join(self._cacher_dir, install_id))
        

class DirectoryCache(object):
    def __init__(self, cache_dir):
        self._cache_dir = cache_dir
        self.build_dir = self._cache_dir

    def already_built(self):
        return os.path.exists(self._cache_dir)
        
    def __enter__(self):
        # TODO: lock
        return self
        
    def __exit__(self, *args):
        pass

# TODO: eurgh, what a horrible name
class NoCachingStrategy(object):
    def cache_for_install(self, install_id):
        return NoCache(os.path.join(tempfile.mkdtemp(), "build"))
        

class NoCache(object):
    def  __init__(self, build_dir):
        self.build_dir = build_dir
    
    def already_built(self):
        return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        shutil.rmtree(self.build_dir)
