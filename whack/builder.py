import os
import subprocess

from . import downloads
from .tempdir import create_temporary_dir
from .naming import name_package
from .common import WHACK_ROOT, PackageNotAvailableError
from .files import mkdir_p, write_file


def build(package_src, params, package_dir):
    with create_temporary_dir() as build_dir:
        _build_in_dir(package_src, build_dir, package_dir, params)


def _build_in_dir(package_src, build_dir, package_dir, params):
    package_src.write_to(build_dir)
        
    build_env = _params_to_build_env(params)
    _fetch_downloads(build_dir, build_env)
        
    build_script = os.path.join(build_dir, "whack/build")
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
        name_package(package_src, params)
    )


def _fetch_downloads(build_dir, build_env):
    downloads_file_path = os.path.join(build_dir, "whack/downloads")
    downloads.fetch_downloads(downloads_file_path, build_env, build_dir)


def _params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env
