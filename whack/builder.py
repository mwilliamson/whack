import os
import dodge

from .tempdir import create_temporary_dir
from .common import WHACK_ROOT
from .files import mkdir_p, write_file
from .errors import FileNotFoundError
from .env import params_to_env
from . import local


class Builder(object):
    def __init__(self, downloader):
        self._downloader = downloader
        
    def build(self, package_request, package_dir):
        # TODO: possibly should always create a tarball and pick package_dir ourselves
        # to ensure it's long enough to allow substitution
        with create_temporary_dir() as build_dir:
            self._build_in_dir(package_request, build_dir, package_dir)


    def _build_in_dir(self, package_request, build_dir, package_dir):
        params = package_request.params()
        
        package_request.write_source_to(build_dir)
        
        build_script = "whack/build"
        build_script_path = os.path.join(build_dir, build_script)
        if not os.path.exists(build_script_path):
            message = "{0} script not found in package source {1}".format(
                build_script, package_request.source_uri
            )
            raise FileNotFoundError(message)
        
        build_env = params_to_env(params)
        self._fetch_downloads(build_dir, build_env)
        
        dist_dir = os.path.join(package_dir, "dist")
        mkdir_p(dist_dir)
        build_command = [
            build_script_path,
            os.path.abspath(dist_dir),
        ]
        local.run(build_command, cwd=build_dir, update_env=build_env)
        write_file(
            os.path.join(package_dir, ".whack-package.json"),
            dodge.dumps(package_request.describe())
        )
        
        mkdir_p(os.path.join(package_dir, "src"))
        package_request.write_source_to(os.path.join(package_dir, "src"))
        
        write_file(
            os.path.join(package_dir, "dist-path"),
            dist_dir,
        )


    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        self._downloader.fetch_downloads(downloads_file_path, build_env, build_dir)
