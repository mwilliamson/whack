import os
import random
import string

import dodge

from .tempdir import create_temporary_dir
from .common import WHACK_ROOT
from .files import mkdir_p, write_file
from .errors import FileNotFoundError
from .env import params_to_env
from . import local
from .tarballs import create_tarball


class Builder(object):
    def __init__(self, downloader):
        self._downloader = downloader
        
    def build(self, package_request, destination_path):
        with create_temporary_dir() as temp_dir:
            build_dir = os.path.join(temp_dir, "build")
            mkdir_p(build_dir)
            # Creating a long path makes it likely that the final destination
            # path will be shorter, allowing the string to be replaced
            # without affecting other bytes
            package_dir = os.path.join(temp_dir, self._generate_long_path())
            self._build_in_dir(package_request, build_dir, package_dir)
            create_tarball(destination_path, source=package_dir)

    def _generate_long_path(self):
        parts = [
            "".join(random.choice(string.ascii_lowercase + string.digits) for character_index in range(100))
            for part_index in range(10)
        ]
        return os.path.join(*parts)


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
