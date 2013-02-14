import os
import uuid
import subprocess
import stat

from .common import WHACK_ROOT


class PackageDeployer(object):
    def deploy(self, install_dir):
        with open(os.path.join(install_dir, "run"), "w") as run_file:
            run_file.write(
                '#!/usr/bin/env sh\n' +
                'PATH=$(dirname $0)/sbin:$(dirname $0)/bin:$PATH\n' +
                'exec whack-run "$(dirname $0)" "$@"'
            )
        subprocess.check_call(["chmod", "+x", os.path.join(install_dir, "run")])
        
        whack_root_id = str(uuid.uuid4())
        
        _create_directly_executable_dir(install_dir, "bin", whack_root_id)
        _create_directly_executable_dir(install_dir, "sbin", whack_root_id)
        
        with open(os.path.join(install_dir, ".whack-root-id"), "w") as root_id_file:
            root_id_file.write(whack_root_id)

def _create_directly_executable_dir(install_dir, bin_dir_name, whack_root_id):
    def install_path(path):
        return os.path.join(install_dir, path)
    
    dot_bin_dir = install_path(".{0}".format(bin_dir_name))
    bin_dir = install_path(bin_dir_name)
    if os.path.exists(dot_bin_dir):
        if not os.path.exists(bin_dir):
            os.mkdir(bin_dir)
        for bin_filename in _list_missing_executable_files(install_dir, dot_bin_dir, bin_dir):
            bin_file_path = os.path.join(bin_dir, bin_filename)
            with open(bin_file_path, "w") as bin_file:
                bin_file.write(
                    '#!/usr/bin/env sh\n\n' +
                    'ACTIVE_ROOT_ID_FILE=\'{0}\'/.whack-root-id\n'.format(WHACK_ROOT) +
                    'MY_ROOT_ID=\'{0}\'\n'.format(whack_root_id) +
                    'ACTIVE_ROOT_ID=`cat "$ACTIVE_ROOT_ID_FILE" 2>/dev/null`\n' +
                    'TARGET="{0}/.{1}/{2}"\n'.format(WHACK_ROOT, bin_dir_name, bin_filename) +
                    'if [ -f "$ACTIVE_ROOT_ID_FILE" ] && [ "$MY_ROOT_ID" = "$ACTIVE_ROOT_ID" ]; then\n' +
                    'exec "$TARGET" "$@"\n' +
                    'else\n' +
                    'exec "$(dirname $0)/../run" "$TARGET" "$@"\n' +
                    'fi\n'
                )
            os.chmod(bin_file_path, 0755)

def _list_missing_executable_files(root_dir, dot_bin_dir, bin_dir):
    def is_missing(filename):
        return not os.path.exists(os.path.join(bin_dir, filename))
    return filter(is_missing, _list_executable_files(root_dir, dot_bin_dir))

def _list_executable_files(root_dir, dir_path):
    def is_executable_file(filename):
        path = os.path.join(dir_path, filename)
        while os.path.islink(path):
            link_target = os.readlink(path)
            if os.path.exists(link_target):
                # Valid symlink
                path = link_target
            elif link_target.startswith("{0}/".format(WHACK_ROOT)):
                # Valid symlink, but whack root isn't mounted
                path = os.path.join(root_dir, link_target[len(WHACK_ROOT) + 1:])
            else:
                # Broken symlink
                return False
        
        if os.path.exists(path):
            is_executable = stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
            return not os.path.isdir(path) and is_executable
        else:
            return False
            
    return filter(is_executable_file, os.listdir(dir_path))
