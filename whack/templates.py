import os
import subprocess
import shutil
import json
import uuid
import stat
import contextlib

import spur

from whack import downloads
from whack.hashes import Hasher
from whack.tempdir import create_temporary_dir


local_shell = spur.LocalShell()
_WHACK_ROOT = "/usr/local/whack"


# TODO: can we combine the two templates by indicating which binaries are
# relocatable within the package source, rather than apply relocatibility to
# the package as a whole?
class RelocatableTemplate(object):
    def build(self, run, build_dir, target_dir):
        build_script = os.path.join(build_dir, "whack/build")
        run([build_script])
        local_shell.run(["cp", "-rT", build_dir, target_dir])
        
    def install(self, build_target_dir, install_dir):
        local_shell.run(
            [os.path.join(build_target_dir, "whack/install"), install_dir],
            cwd=build_target_dir
        )
     
        
class FixedRootTemplate(object):
    def build(self, run, build_dir, target_dir):
        install_script = os.path.join(build_dir, "whack/install")
        os.mkdir(target_dir)
        run([
            "whack-run-with-whack-root",
            target_dir,
            install_script,
            _WHACK_ROOT
        ])
                
        with open(os.path.join(target_dir, "run"), "w") as run_file:
            run_file.write('#!/usr/bin/env sh\nexec whack-run-with-whack-root "$(dirname $0)" "$@"')
        subprocess.check_call(["chmod", "+x", os.path.join(target_dir, "run")])
        
        self._create_bin_dir(target_dir, "bin")
        self._create_bin_dir(target_dir, "sbin")
    
    def _create_bin_dir(self, install_dir, bin_dir_name):
        def install_path(path):
            return os.path.join(install_dir, path)
        
        dot_bin_dir = install_path(".{0}".format(bin_dir_name))
        bin_dir = install_path(bin_dir_name)
        if os.path.exists(dot_bin_dir):
            if not os.path.exists(bin_dir):
                os.mkdir(bin_dir)
            for bin_filename in self._list_missing_executable_files(install_dir, dot_bin_dir, bin_dir):
                bin_file_path = os.path.join(bin_dir, bin_filename)
                with open(bin_file_path, "w") as bin_file:
                    bin_file.write(
                        '#!/usr/bin/env sh\n\n' +
                        'TARGET="$(dirname $0)/../.{0}/{1}"\n'.format(bin_dir_name, bin_filename) +
                        'ACTIVE_ROOT_ID_FILE=\'{0}\'\n'.format(_WHACK_ROOT) +
                        'MY_ROOT_ID=`cat $(dirname $0)/../.whack-root-id`\n' +
                        'ACTIVE_ROOT_ID=`cat "$ACTIVE_ROOT_ID_FILE" 2>/dev/null`\n' +
                        'if [ -f "$ACTIVE_ROOT_ID_FILE" ] && [ "$MY_ROOT_ID" = "$ACTIVE_ROOT_ID" ]; then\n' +
                        'exec "$TARGET" "$@"\n' +
                        'else\n' +
                        'exec "$(dirname $0)/../run" "$TARGET" "$@"\n' +
                        'fi\n'
                    )
                os.chmod(bin_file_path, 0755)
    
    def _list_missing_executable_files(self, root_dir, dot_bin_dir, bin_dir):
        def is_missing(filename):
            return not os.path.exists(os.path.join(bin_dir, filename))
        return filter(is_missing, self._list_executable_files(root_dir, dot_bin_dir))
    
    def _list_executable_files(self, root_dir, dir_path):
        def is_executable_file(filename):
            path = os.path.join(dir_path, filename)
            while os.path.islink(path):
                link_target = os.readlink(path)
                if os.path.exists(link_target):
                    # Valid symlink
                    path = link_target
                elif link_target.startswith("{0}/".format(_WHACK_ROOT)):
                    # Valid symlink, but what root isn't mounted
                    path = os.path.join(root_dir, link_target[len(_WHACK_ROOT) + 1:])
                else:
                    # Broken symlink
                    return False
            
            if os.path.exists(path):
                is_executable = stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
                return not os.path.isdir(path) and is_executable
            else:
                return False
                
        return filter(is_executable_file, os.listdir(dir_path))
    
    def install(self, build_target_dir, install_dir):
        # TODO: should be pure Python, but there isn't a stdlib function
        # that allows the destination to already exist
        subprocess.check_call(["cp", "-rT", build_target_dir, install_dir])
        with open(os.path.join(install_dir, ".whack-root-id"), "w") as root_id_file:
            root_id_file.write(str(uuid.uuid4()))


def template(name):
    return _templates[name]


_templates = {
    "fixed-root": FixedRootTemplate(),
    "relocatable": RelocatableTemplate()
}
