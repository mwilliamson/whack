import os
import subprocess

from nose.tools import istest, assert_equal

import whack.operations
import whack.config
import testing
from whack.tempdir import create_temporary_dir

@istest
def application_is_installed_by_running_build_then_install_scripts():
    test_install(
        build=testing.HelloWorld.BUILD,
        install=testing.HelloWorld.INSTALL,
        expected_output=testing.HelloWorld.EXPECTED_OUTPUT
    )

@istest
def version_is_passed_to_build_script():
    _TEST_BUILDER_BUILD = r"""#!/bin/sh
echo '#!/bin/sh' >> hello
echo echo ${VERSION} >> hello
chmod +x hello
"""

    _TEST_BUILDER_INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""
    test_install(
        build=_TEST_BUILDER_BUILD,
        install=_TEST_BUILDER_INSTALL,
        expected_output="1\n"
    )
    

@istest
def package_from_source_control_can_be_downloaded_and_used():
    with create_temporary_dir() as package_dir, create_temporary_dir() as install_dir:
        testing.write_package(package_dir, testing.HelloWorld.BUILD, testing.HelloWorld.INSTALL)
        _convert_to_git_repo(package_dir)
        
        _install(
            "git+file://{0}".format(package_dir),
            install_dir
        )
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)


@istest
def package_from_local_filesystem_can_be_used():
    with create_temporary_dir() as package_dir, create_temporary_dir() as install_dir:
        testing.write_package(package_dir, testing.HelloWorld.BUILD, testing.HelloWorld.INSTALL)
        
        _install(package_dir, install_dir)
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)


def _convert_to_git_repo(cwd):
    def _git(command):
        subprocess.check_call(["git"] + command, cwd=cwd)
    _git(["init"])
    _git(["add", "."])
    _git(["commit", "-m", "Initial commit"])

def test_install(build, install, expected_output):
    for should_cache in [True, False]:
        caching = whack.config.caching_config(enabled=should_cache)
        test_install_with_caching(build, install, expected_output, caching=caching)

def test_install_with_caching(build, install, expected_output, caching):
    with create_temporary_dir() as repo_dir, create_temporary_dir() as install_dir:
        testing.create_test_builder(repo_dir, build, install)
        
        _install(
            "hello",
            install_dir,
            builder_uris=[repo_dir],
            params={"version": "1"},
            caching=caching
        )
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal(expected_output, output)
    

def _install(package, install_dir, caching=None, params=None, builder_uris=None):
    if caching is None:
        caching = whack.config.caching_config(enabled=False)
    whack.operations.install(
        package,
        install_dir,
        caching=caching,
        builder_uris=builder_uris,
        params=params
    )
