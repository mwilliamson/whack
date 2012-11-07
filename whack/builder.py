import os
import os.path
import subprocess
import shutil
import contextlib
import tempfile

from whack import downloads
from whack.hashes import Hasher

class Builders(object):
    def __init__(self, should_cache, builder_repo_uris):
        self._should_cache = should_cache
        self._builder_repo_urls = builder_repo_uris

    def build_and_install(self, package, install_dir):
        package_name, package_version = package.split("=")
        scripts_dir = self._fetch_scripts(package_name)
        builder = Builder(self._should_cache, scripts_dir, package_version)
        return builder.build_and_install(install_dir)

    def _fetch_scripts(self, package):
        for uri in self._builder_repo_urls:
            if self._is_local_uri(uri):
                repo_dir = uri
            else:
                repo_dir = downloads.fetch_source_control_uri(uri)
            # FIXME: race condition between this and when we acquire the lock
            package_dir = os.path.join(repo_dir, package)
            if os.path.exists(package_dir):
                return package_dir
                
        raise RuntimeError("No builders found for package: {0}".format(package))
        
    def _is_local_uri(self, uri):
        return "://" not in uri

class Builder(object):
    def __init__(self, should_cache, scripts_dir, package_version):
        self._should_cache = should_cache
        self._scripts_dir = scripts_dir
        self._package_version = package_version
    
    def build_and_install(self, install_dir):
        with self._build_dir_for() as build_dir:
            if not self._already_built(build_dir):
                self._build(build_dir)
            
            self._install(build_dir, install_dir)

    def _already_built(self, build_dir):
        return os.path.exists(build_dir)

    def _build(self, build_dir):
        try:
            ignore = shutil.ignore_patterns(".svn", ".hg", ".hgignore", ".git", ".gitignore")
            shutil.copytree(self._scripts_dir, build_dir, ignore=ignore)
            self._fetch_downloads(build_dir)
            
            build_env = os.environ.copy()
            build_env["VERSION"] = self._package_version
            subprocess.check_call(
                [os.path.join(self._scripts_dir, "build")],
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

    def _install(self, build_dir, install_dir):
        subprocess.check_call(
            [os.path.join(build_dir, "install"), install_dir],
            cwd=build_dir
        )

    @contextlib.contextmanager
    def _build_dir_for(self):
        if self._should_cache:
            dir_name = self._generate_build_dir()
            yield os.path.join(os.path.expanduser("~/.cache/whack/builds"), dir_name)
        else:
            try:
                build_dir = tempfile.mkdtemp()
                yield os.path.join(build_dir, "build")
            finally:
                shutil.rmtree(build_dir)

    def _generate_build_dir(self):
        hasher = Hasher()
        hasher.update_with_dir(self._scripts_dir)
        hasher.update(self._package_version)
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

