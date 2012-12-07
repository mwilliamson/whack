import os
import subprocess

from nose.tools import istest, assert_equal

import testing
from testing import temporary_dir

@istest
def application_is_installed_by_running_build_then_install_scripts():
    with temporary_dir() as repo_dir, temporary_dir() as install_dir:
        testing.create_test_builder(
            repo_dir,
            testing.HelloWorld.BUILD,
            testing.HelloWorld.INSTALL
        )
        
        subprocess.check_call(["whack", "install", "hello=1", install_dir, "--add-builder-repo", repo_dir])
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)

