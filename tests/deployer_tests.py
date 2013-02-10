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
            _sh_script_description("bin/hello", "cat {0}/message".format(WHACK_ROOT)),
        ])
        deployer = PackageDeployer()
        deployer.deploy(package_dir, install_dir)
        
        command = [os.path.join(install_dir, "run"), "hello"]
        output = subprocess.check_output(command)
        assert_equal("Hello there", output)


@istest
def placing_executables_under_dot_bin_creates_directly_executable_files_under_bin():
    with create_temporary_dir() as package_dir, create_temporary_dir() as install_dir:
        _write_files(package_dir, [
            FileDescription("message", "Hello there"),
            _sh_script_description(".bin/hello", "cat {0}/message".format(WHACK_ROOT)),
        ])
        deployer = PackageDeployer()
        deployer.deploy(package_dir, install_dir)
        
        command = [os.path.join(install_dir, "bin/hello")]
        output = subprocess.check_output(command)
        assert_equal("Hello there", output)
    
    
@istest
def placing_executables_under_dot_sbin_creates_directly_executable_files_under_sbin():
    with create_temporary_dir() as package_dir, create_temporary_dir() as install_dir:
        _write_files(package_dir, [
            FileDescription("message", "Hello there"),
            _sh_script_description(".sbin/hello", "cat {0}/message".format(WHACK_ROOT)),
        ])
        deployer = PackageDeployer()
        deployer.deploy(package_dir, install_dir)
        
        command = [os.path.join(install_dir, "sbin/hello")]
        output = subprocess.check_output(command)
        assert_equal("Hello there", output)


@istest
def files_already_under_bin_are_not_replaced():
    with create_temporary_dir() as package_dir, create_temporary_dir() as install_dir:
        _write_files(package_dir, [
            _sh_script_description("bin/hello", "echo Hello from bin"),
            _sh_script_description(".bin/hello", "echo Hello from .bin"),
        ])
        deployer = PackageDeployer()
        deployer.deploy(package_dir, install_dir)
        
        command = [os.path.join(install_dir, "bin/hello")]
        output = subprocess.check_output(command)
        assert_equal("Hello from bin\n", output)
    
    
@istest
def non_executable_files_under_dot_bin_are_not_created_in_bin():
    with create_temporary_dir() as package_dir, create_temporary_dir() as install_dir:
        _write_files(package_dir, [
            FileDescription(".bin/message", "Hello there"),
        ])
        deployer = PackageDeployer()
        deployer.deploy(package_dir, install_dir)
        
        assert not os.path.exists(os.path.join(install_dir, "bin/message"))


def _write_files(root_dir, file_descriptions):
    for file_description in file_descriptions:
        path = os.path.join(root_dir, file_description.path)
        mkdir_p(os.path.dirname(path))
        write_file(path, file_description.contents)
        os.chmod(path, file_description.permissions)


def _sh_script_description(path, contents):
    return FileDescription(path, "#!/bin/sh\n{0}".format(contents), 0755)


class FileDescription(object):
    def __init__(self, path, contents, permissions=0644):
        self.path = path
        self.contents = contents
        self.permissions = permissions
