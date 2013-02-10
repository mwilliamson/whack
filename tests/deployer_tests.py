import os
import subprocess

from nose.tools import istest, assert_equal

from whack.common import WHACK_ROOT
from whack.deployer import PackageDeployer
from whack.tempdir import create_temporary_dir
from whack.files import write_file, mkdir_p


@istest
def run_script_in_installation_mounts_whack_root_before_running_command():
    with create_temporary_dir() as package_dir, create_temporary_dir() as install_dir:
        _write_files(package_dir, [
            FileDescription("message", "Hello there"),
            FileDescription("bin/hello", "#!/bin/sh\ncat {0}/message".format(WHACK_ROOT), 0755),
        ])
        deployer = PackageDeployer()
        deployer.deploy(package_dir, install_dir)
        
        command = [os.path.join(install_dir, "run"), "hello"]
        output = subprocess.check_output(command)
        assert_equal("Hello there", output)


def _write_files(root_dir, file_descriptions):
    for file_description in file_descriptions:
        path = os.path.join(root_dir, file_description.path)
        mkdir_p(os.path.dirname(path))
        write_file(path, file_description.contents)
        os.chmod(path, file_description.permissions)
    
    
class FileDescription(object):
    def __init__(self, path, contents, permissions=0644):
        self.path = path
        self.contents = contents
        self.permissions = permissions
