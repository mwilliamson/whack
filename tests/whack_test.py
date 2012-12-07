import os
import subprocess

from nose.tools import istest, assert_equal

from whack.builder import Builders
import testing
from testing import temporary_dir

@istest
def application_is_installed_by_running_build_then_install_scripts():
    test_single_build(
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
    test_single_build(
        build=_TEST_BUILDER_BUILD,
        install=_TEST_BUILDER_INSTALL,
        expected_output="1\n"
    )

def test_single_build(build, install, expected_output):
    for should_cache in [True, False]:
        with temporary_dir() as repo_dir, temporary_dir() as install_dir:
            testing.create_test_builder(repo_dir, build, install)
            
            builders = Builders(should_cache=should_cache, builder_repo_uris=[repo_dir])
            builders.build_and_install("hello", install_dir, {"version": "1"})
            
            output = subprocess.check_output([os.path.join(install_dir, "hello")])
            assert_equal(expected_output, output)

