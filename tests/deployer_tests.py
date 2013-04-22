import os
import tempfile
import shutil

from nose.tools import istest, assert_equal

from whack.common import WHACK_ROOT
from whack.deployer import PackageDeployer
from whack.files import \
    write_files, sh_script_description, directory_description, plain_file, \
    symlink
from whack import local


@istest
def run_script_in_installation_mounts_whack_root_before_running_command():
    deployed_package = _deploy_package([
        plain_file("message", "Hello there"),
        sh_script_description("bin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ])
    with deployed_package:
        command = [
            deployed_package.path("run"),
            deployed_package.path("bin/hello")
        ]
        _assert_output(command, "Hello there")


@istest
def path_environment_variable_includes_bin_directory_under_whack_root():
    deployed_package = _deploy_package([
        sh_script_description("bin/hello", "echo Hello there"),
    ])
    with deployed_package:
        command = [deployed_package.path("run"), "hello"]
        _assert_output(command, "Hello there\n")


@istest
def path_environment_variable_includes_sbin_directory_under_whack_root():
    deployed_package = _deploy_package([
        sh_script_description("sbin/hello", "echo Hello there"),
    ])
    with deployed_package:
        command = [deployed_package.path("run"), "hello"]
        _assert_output(command, "Hello there\n")


@istest
def placing_executables_under_dot_bin_creates_directly_executable_files_under_bin():
    deployed_package = _deploy_package([
        plain_file("message", "Hello there"),
        sh_script_description(".bin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ])
    with deployed_package:
        command = [deployed_package.path("bin/hello")]
        _assert_output(command, "Hello there")
    
    
@istest
def placing_executables_under_dot_sbin_creates_directly_executable_files_under_sbin():
    deployed_package = _deploy_package([
        plain_file("message", "Hello there"),
        sh_script_description(".sbin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ])
    with deployed_package:
        command = [deployed_package.path("sbin/hello")]
        _assert_output(command, "Hello there")


@istest
def files_already_under_bin_are_not_replaced():
    deployed_package = _deploy_package([
        sh_script_description("bin/hello", "echo Hello from bin"),
        sh_script_description(".bin/hello", "echo Hello from .bin"),
    ])
    with deployed_package:
        command = [deployed_package.path("bin/hello")]
        _assert_output(command, "Hello from bin\n")
    
    
@istest
def non_executable_files_under_dot_bin_are_not_created_in_bin():
    deployed_package = _deploy_package([
        plain_file(".bin/message", "Hello there"),
    ])
    with deployed_package:
        assert not os.path.exists(deployed_package.path("bin/message"))
    
    
@istest
def directories_under_dot_bin_are_not_created_in_bin():
    deployed_package = _deploy_package([
        directory_description(".bin/sub"),
    ])
    with deployed_package:
        assert not os.path.exists(deployed_package.path("bin/sub"))
    
    
@istest
def working_symlinks_in_dot_bin_to_files_under_whack_root_are_created_in_bin():
    deployed_package = _deploy_package([
        sh_script_description(".bin/hello", "echo Hello there"),
        symlink(".bin/hello-sym", os.path.join(WHACK_ROOT, ".bin/hello")),
        symlink(".bin/hello-borked", os.path.join(WHACK_ROOT, ".bin/hell")),
    ])
    with deployed_package:
        command = [deployed_package.path("bin/hello-sym")]
        _assert_output(command, "Hello there\n")
        assert not os.path.exists(deployed_package.path("bin/hello-borked"))
    
    
@istest
def relative_symlinks_in_dot_bin_are_created_in_bin():
    deployed_package = _deploy_package([
        plain_file("message", "Hello there"),
        sh_script_description("sub/bin/hello", "cat {0}/message".format(WHACK_ROOT)),
        symlink(".bin", "sub/bin"),
    ])
    with deployed_package:
        command = [deployed_package.path("bin/hello")]
        _assert_output(command, "Hello there")


@istest
def placing_executables_under_symlinked_dot_bin_creates_directly_executable_files_under_bin():
    deployed_package = _deploy_package([
        plain_file("message", "Hello there"),
        sh_script_description("sub/bin/hello", "cat {0}/message".format(WHACK_ROOT)),
        symlink(".bin", os.path.join(WHACK_ROOT, "sub/bin")),
    ])
    with deployed_package:
        command = [deployed_package.path("bin/hello")]
        _assert_output(command, "Hello there")


@istest
def whack_root_is_not_remounted_if_executing_scripts_under_whack_root():
    deployed_package = _deploy_package([
        sh_script_description(".bin/hello", "echo Hello there"),
        sh_script_description(".bin/hello2", "{0}/bin/hello".format(WHACK_ROOT)),
    ])
    with deployed_package:
        _add_echo_to_run_command(deployed_package)
        command = [deployed_package.path("bin/hello2")]
        _assert_output(command, "Run!\nHello there\n")


@istest
def whack_root_is_remounted_if_in_different_whack_root():
    first_deployed_package = _deploy_package([
        plain_file("message", "Hello there"),
        sh_script_description(".bin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ])
    with first_deployed_package:
        hello_path = first_deployed_package.path("bin/hello")
        second_deployed_package = _deploy_package([
            sh_script_description(".bin/hello2", "{0}".format(hello_path)),
        ])
        with second_deployed_package:
            _add_echo_to_run_command(first_deployed_package)
            _add_echo_to_run_command(second_deployed_package)
            command = [second_deployed_package.path("bin/hello2")]
            _assert_output(command, "Run!\nRun!\nHello there")


def _add_echo_to_run_command(deployed_package):
    # This is a huge honking hack. I'm sorry.
    run_command_path = deployed_package.path("run")
    with open(run_command_path) as run_command_file:
        run_contents = run_command_file.read()
    run_contents = run_contents.replace("\n", "\necho Run!\n", 1)
    with open(run_command_path, "w") as run_command_file:
        run_command_file.write(run_contents)
    


def _deploy_package(file_descriptions):
    package_dir = tempfile.mkdtemp()
    try:
        write_files(package_dir, file_descriptions)
        deployer = PackageDeployer()
        deployer.deploy(package_dir)
        return DeployedPackage(package_dir)
    except:
        shutil.rmtree(package_dir)
        raise


def _assert_output(command, expected_output):
    output = local.run(command).output
    assert_equal(expected_output, output)


class DeployedPackage(object):
    def __init__(self, package_dir):
        self._package_dir = package_dir
        
    def path(self, path):
        return os.path.join(self._package_dir, path)
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        shutil.rmtree(self._package_dir)
