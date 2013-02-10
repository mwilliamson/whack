import os
import uuid
import subprocess

from .files import copy_dir
from .executables import create_directly_executable_dir


class PackageDeployer(object):
    def deploy(self, package_source, package_dir, install_dir):
        copy_dir(package_dir, install_dir)
                
        with open(os.path.join(install_dir, "run"), "w") as run_file:
            run_file.write('#!/usr/bin/env sh\nexec whack-run-with-whack-root "$(dirname $0)" "$@"')
        subprocess.check_call(["chmod", "+x", os.path.join(install_dir, "run")])
        
        create_directly_executable_dir(install_dir, "bin")
        create_directly_executable_dir(install_dir, "sbin")
        
        with open(os.path.join(install_dir, ".whack-root-id"), "w") as root_id_file:
            root_id_file.write(str(uuid.uuid4()))
