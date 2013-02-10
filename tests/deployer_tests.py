import os
import subprocess
import tempfile
import shutil

from nose.tools import istest, assert_equal

from whack.common import WHACK_ROOT
from whack.deployer import PackageDeployer
from whack.tempdir import create_temporary_dir
from whack.files import write_file, mkdir_p


@istest
def run_script_in_installation_mounts_whack_root_before_running_command():
    deployed_package = _deploy_package([
        _plain_file("message", "Hello there"),
        _sh_script_description("bin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ])
    with deployed_package:
        command = [deployed_package.path("run"), "hello"]
        output = subprocess.check_output(command)
        assert_equal("Hello there", output)


@istest
def placing_executables_under_dot_bin_creates_directly_executable_files_under_bin():
    deployed_package = _deploy_package([
        _plain_file("message", "Hello there"),
        _sh_script_description(".bin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ])
    with deployed_package:
        command = [deployed_package.path("bin/hello")]
        output = subprocess.check_output(command)
        assert_equal("Hello there", output)
    
    
@istest
def placing_executables_under_dot_sbin_creates_directly_executable_files_under_sbin():
    deployed_package = _deploy_package([
        _plain_file("message", "Hello there"),
        _sh_script_description(".sbin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ])
    with deployed_package:
        command = [deployed_package.path("sbin/hello")]
        output = subprocess.check_output(command)
        assert_equal("Hello there", output)


@istest
def files_already_under_bin_are_not_replaced():
    deployed_package = _deploy_package([
        _sh_script_description("bin/hello", "echo Hello from bin"),
        _sh_script_description(".bin/hello", "echo Hello from .bin"),
    ])
    with deployed_package:
        output = subprocess.check_output([deployed_package.path("bin/hello")])
        assert_equal("Hello from bin\n", output)
    
    
@istest
def non_executable_files_under_dot_bin_are_not_created_in_bin():
    deployed_package = _deploy_package([
        _plain_file(".bin/message", "Hello there"),
    ])
    with deployed_package:
        assert not os.path.exists(deployed_package.path("bin/message"))
    
    
@istest
def directories_under_dot_bin_are_not_created_in_bin():
    deployed_package = _deploy_package([
        _directory_description(".bin/sub"),
    ])
    with deployed_package:
        assert not os.path.exists(deployed_package.path("bin/sub"))
    
    
@istest
def working_symlinks_in_dot_bin_to_files_under_whack_root_are_created_in_bin():
    deployed_package = _deploy_package([
        _sh_script_description(".bin/hello", "echo Hello there"),
        _symlink(".bin/hello-sym", os.path.join(WHACK_ROOT, ".bin/hello")),
        _symlink(".bin/hello-borked", os.path.join(WHACK_ROOT, ".bin/hell")),
    ])
    with deployed_package:
        output = subprocess.check_output([deployed_package.path("bin/hello-sym")])
        assert_equal("Hello there\n", output)
        assert not os.path.exists(deployed_package.path("bin/hello-borked"))


def _deploy_package(file_descriptions):
    package_dir = tempfile.mkdtemp()
    try:
        install_dir = tempfile.mkdtemp()
        try:
            _write_files(package_dir, file_descriptions)
            deployer = PackageDeployer()
            deployer.deploy(package_dir, install_dir)
            return DeployedPackage(package_dir, install_dir)
        except:
            shutil.rmtree(install_dir)
            raise
    except:
        shutil.rmtree(package_dir)
        raise
        

class DeployedPackage(object):
    def __init__(self, package_dir, install_dir):
        self._package_dir = package_dir
        self._install_dir = install_dir
        
    def path(self, path):
        return os.path.join(self._install_dir, path)
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        shutil.rmtree(self._package_dir)
        shutil.rmtree(self._install_dir)
        

def _write_files(root_dir, file_descriptions):
    for file_description in file_descriptions:
        path = os.path.join(root_dir, file_description.path)
        if file_description.file_type == "dir":
            mkdir_p(path)
        elif file_description.file_type == "file":
            mkdir_p(os.path.dirname(path))
            write_file(path, file_description.contents)
            os.chmod(path, file_description.permissions)
        elif file_description.file_type == "symlink":
            os.symlink(file_description.contents, path)


def _sh_script_description(path, contents):
    return FileDescription(path, "#!/bin/sh\n{0}".format(contents), 0755, "file")


def _directory_description(path):
    return FileDescription(path, None, permissions=None, file_type="dir")


def _plain_file(path, contents):
    return FileDescription(path, contents, permissions=0644, file_type="file")


def _symlink(path, actual_path):
    return FileDescription(path, actual_path, permissions=None, file_type="symlink")


class FileDescription(object):
    def __init__(self, path, contents, permissions, file_type):
        self.path = path
        self.contents = contents
        self.permissions = permissions
        self.file_type = file_type
