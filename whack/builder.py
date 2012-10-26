import os
import os.path
import subprocess
import shutil
import contextlib
import tempfile

from whack import downloads
from whack.hashes import Hasher

def build(package, install_dir, should_cache):
    package_name, package_version = package.split("=")
    scripts_dir = _fetch_scripts(package_name)
    with _build_dir_for(package, scripts_dir, install_dir, should_cache) as build_dir:
        if not _already_built(build_dir):
            _build(scripts_dir, build_dir, install_dir)
        
        _install(scripts_dir, build_dir, install_dir)

def _already_built(build_dir):
    return os.path.exists(build_dir) and os.listdir(build_dir) != []

def _build(scripts_dir, build_dir, install_dir):
    try:
        _fetch_downloads(scripts_dir, build_dir)
        
        subprocess.check_call(
            [os.path.join(scripts_dir, "build"), install_dir],
            cwd=build_dir
        )
    except:
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        raise

def _fetch_downloads(scripts_dir, build_dir):
    downloads_file_path = os.path.join(scripts_dir, "downloads")
    download_urls = _read_downloads_file(downloads_file_path)
    for url in download_urls:
        downloads.download_to_dir(url, build_dir)

def _fetch_scripts(package):
    builders_repo_uri = "git+https://github.com/mwilliamson/whack-builders.git"
    repo_dir = downloads.fetch_source_control_uri(builders_repo_uri)
    # FIXME: race condition between this and when we acquire the lock
    package_dir = os.path.join(repo_dir, package)
    if os.path.exists(package_dir):
        return package_dir
    else:
        raise RuntimeError("No builders found for package: {0}".format(package))

def _install(scripts_dir, build_dir, install_dir):
    subprocess.check_call(
        [os.path.join(scripts_dir, "install"), install_dir],
        cwd=build_dir
    )

@contextlib.contextmanager
def _build_dir_for(package, scripts_dir, install_dir, should_cache):
    if should_cache:
        dir_name = _generate_build_dir(package, scripts_dir, install_dir)
        yield os.path.join(os.path.expanduser("~/.cache/whack/builds"), dir_name)
    else:
        try:
            build_dir = tempfile.mkdtemp()
            yield build_dir
        finally:
            shutil.rmtree(build_dir)

def _generate_build_dir(package, scripts_dir, install_dir):
    hasher = Hasher()
    hasher.update_with_dir(scripts_dir)
    hasher.update(install_dir)
    hasher.update(package)
    return hasher.hexdigest()

def _read_downloads_file(path):
    if os.path.exists(path):
        return [line.strip() for line in open(path) if line]
    else:
        return []
    
if __name__ == "__main__":
    main()

