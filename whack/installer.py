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
        with self._build_dir_for(install_id) as build_dir:
            if not self._already_built(build_dir):
                self._build(build_dir, params)
            
            self._run_install_script(build_dir, install_dir)

    def _already_built(self, build_dir):
        return os.path.exists(build_dir)

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

    @contextlib.contextmanager
    def _build_dir_for(self, install_id):
        if self._should_cache:
            yield os.path.join(os.path.expanduser("~/.cache/whack/builds"), install_id)
        else:
            try:
                build_dir = tempfile.mkdtemp()
                yield os.path.join(build_dir, "build")
            finally:
                shutil.rmtree(build_dir)

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
