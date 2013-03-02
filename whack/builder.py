import os
import subprocess

from . import downloads
from .tempdir import create_temporary_dir
from .common import WHACK_ROOT
from .files import mkdir_p, write_file
from .errors import FileNotFoundError


def build(package_request, package_dir):
    with create_temporary_dir() as build_dir:
        _build_in_dir(package_request, build_dir, package_dir)


def _build_in_dir(package_request, build_dir, package_dir):
    params = package_request.params()
    
    package_request.write_source_to(build_dir)
    
    build_script = os.path.join(build_dir, "whack/build")
    if not os.path.exists(build_script):
        message = "whack/build script not found in package source {0}".format(
            package_request.source_uri
        )
        raise FileNotFoundError(message)
    
    build_env = _params_to_build_env(params)
    _fetch_downloads(build_dir, build_env)
    mkdir_p(package_dir)
    build_command = [
        "whack-run",
        os.path.abspath(package_dir), # package_dir is mounted at WHACK_ROOT
        build_script, # build_script is executed
        WHACK_ROOT # WHACK_ROOT is passed as the first argument to build_script
    ]
    subprocess.check_call(build_command, cwd=build_dir, env=build_env)
    write_file(
        os.path.join(package_dir, ".whack-package-name"),
        package_request.name()
    )


def _fetch_downloads(build_dir, build_env):
    downloads_file_path = os.path.join(build_dir, "whack/downloads")
    downloads.fetch_downloads(downloads_file_path, build_env, build_dir)


def _params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env
