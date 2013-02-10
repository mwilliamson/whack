import os
import subprocess

from nose.tools import istest, assert_equal

import whack.operations
import whack.config
import testing
from whack.tempdir import create_temporary_dir


@istest
def application_is_installed_by_running_build_script_and_copying_output():
    test_install(
        build=testing.HelloWorld.BUILD,
        expected_output=testing.HelloWorld.EXPECTED_OUTPUT
    )


@istest
def version_is_passed_to_build_script():
    _TEST_BUILDER_BUILD = r"""#!/bin/sh
set -e
cd $1
echo '#!/bin/sh' >> hello
echo echo ${VERSION} >> hello
chmod +x hello
"""

    test_install(
        build=_TEST_BUILDER_BUILD,
        expected_output="1\n"
    )


def test_install(build, expected_output):
    for should_cache in [True, False]:
        caching = whack.config.caching_config(enabled=should_cache)
        test_install_with_caching(build, expected_output, caching=caching)

def test_install_with_caching(build, expected_output, caching):
    with create_temporary_dir() as package_source_dir, create_temporary_dir() as install_dir:
        testing.write_package_source(package_source_dir, {"build": build})
        
        _install(
            package_source_dir,
            install_dir,
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
        params=params
    )
