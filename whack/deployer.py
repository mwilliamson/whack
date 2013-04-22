import os
import stat

from .common import WHACK_ROOT
from .files import copy_dir
from . import local


class PackageDeployer(object):
    def deploy(self, package_dir, target_dir=None):
        if target_dir is None:
            install_dir = package_dir
        else:
            install_dir = target_dir
            copy_dir(package_dir, install_dir)
        
        with open(os.path.join(install_dir, "run"), "w") as run_file:
            run_file.write(
                '#!/usr/bin/env sh\n\n' +
                'MY_ROOT=`readlink --canonicalize-missing "$(dirname $0)"`\n' +
                'if [ "$MY_ROOT" = "{0}" ]; then\n'.format(WHACK_ROOT) +
                '   exec "$@"\n' +
                'else\n' +
                '   PATH=$(dirname $0)/sbin:$(dirname $0)/bin:$PATH\n' +
                '   exec whack-run "$MY_ROOT" "$@"\n' +
                'fi\n'
            )
        local.run(["chmod", "+x", os.path.join(install_dir, "run")])
        
        _create_directly_executable_dir(install_dir, "bin")
        _create_directly_executable_dir(install_dir, "sbin")
        

def _create_directly_executable_dir(install_dir, bin_dir_name):
    def install_path(path):
        return os.path.join(install_dir, path)
    
    dot_bin_dir = install_path(".{0}".format(bin_dir_name))
    dot_bin_dir = _follow_symlinks_in_whack_root(install_dir, dot_bin_dir)
    bin_dir = install_path(bin_dir_name)
    if dot_bin_dir is not None and os.path.exists(dot_bin_dir):
        if not os.path.exists(bin_dir):
            os.mkdir(bin_dir)
        for bin_filename in _list_missing_executable_files(install_dir, dot_bin_dir, bin_dir):
            bin_file_path = os.path.join(bin_dir, bin_filename)
            with open(bin_file_path, "w") as bin_file:
                bin_file.write(
                    '#!/usr/bin/env sh\n\n' +
                    'MY_ROOT=`readlink --canonicalize-missing "$(dirname $0)/.."`\n' +
                    'TARGET="{0}/.{1}/{2}"\n'.format(WHACK_ROOT, bin_dir_name, bin_filename) +
                    'exec "$MY_ROOT/run" "$TARGET" "$@"\n'
                )
            os.chmod(bin_file_path, 0755)

def _list_missing_executable_files(root_dir, dot_bin_dir, bin_dir):
    def is_missing(filename):
        return not os.path.exists(os.path.join(bin_dir, filename))
    return filter(is_missing, _list_executable_files(root_dir, dot_bin_dir))


def _list_executable_files(root_dir, dir_path):
    def is_executable_file(filename):
        path = os.path.join(dir_path, filename)
        return _is_executable_file_in_whack_root(root_dir, path)
            
    return filter(is_executable_file, os.listdir(dir_path))


def _is_executable_file_in_whack_root(root_dir, path):
    path = _follow_symlinks_in_whack_root(root_dir, path)
    
    if path is not None and os.path.exists(path):
        is_executable = stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
        return not os.path.isdir(path) and is_executable
    else:
        return False


def _follow_symlinks_in_whack_root(root_dir, path):
    while os.path.islink(path):
        link_target = os.path.join(os.path.dirname(path), os.readlink(path))
        if os.path.exists(link_target):
            # Valid symlink
            path = link_target
        elif link_target.startswith("{0}/".format(WHACK_ROOT)):
            # Valid symlink, but whack root isn't mounted
            path = os.path.join(root_dir, link_target[len(WHACK_ROOT) + 1:])
        else:
            # Broken symlink
            return None
            
    return path
