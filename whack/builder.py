import os
import subprocess

from .tempdir import create_temporary_dir
from .common import WHACK_ROOT
from .files import mkdir_p, write_file
from .errors import FileNotFoundError
from .env import params_to_env


class Builder(object):
    def __init__(self, downloader):
        self._downloader = downloader
        
    def build(self, package_request, package_dir):
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
        mkdir_p(package_dir)
        build_command = [
            "whack-run",
            os.path.abspath(package_dir), # package_dir is mounted at WHACK_ROOT
            build_script_path, # build_script is executed
            WHACK_ROOT # WHACK_ROOT is passed as the first argument to build_script
        ]
        subprocess.check_call(build_command, cwd=build_dir, env=build_env)
        write_file(
            os.path.join(package_dir, ".whack-package-name"),
            package_request.name()
        )


    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        self._downloader.fetch_downloads(downloads_file_path, build_env, build_dir)
