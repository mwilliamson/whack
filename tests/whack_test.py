import os
import subprocess
import functools
import contextlib

from nose.tools import assert_equal

import whack.operations
import whack.config
import testing
from whack.tempdir import create_temporary_dir
from . import test_sets


test_set = test_sets.TestSetBuilder()

test = test_set.add_test


@test
def application_is_installed_by_running_build_script_and_copying_output(ops):
    test_install(
        ops,
        build=testing.HelloWorld.BUILD,
        expected_output=testing.HelloWorld.EXPECTED_OUTPUT
    )


@test
def version_is_passed_to_build_script(ops):
    _TEST_BUILDER_BUILD = r"""#!/bin/sh
set -e
cd $1
echo '#!/bin/sh' >> hello
echo echo ${VERSION} >> hello
chmod +x hello
"""

    test_install(
        ops,
        build=_TEST_BUILDER_BUILD,
        expected_output="1\n"
    )


def test_install(ops, build, expected_output):
    with create_temporary_dir() as package_source_dir, create_temporary_dir() as install_dir:
        testing.write_package_source(package_source_dir, {"build": build})
        
        ops.install(
            package_source_dir,
            install_dir,
            params={"version": "1"},
        )
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal(expected_output, output)


def _run_test(caching, test_func):
    with _temporary_xdg_cache_dir():
        ops = whack.operations.create(caching)
        return test_func(ops)


@contextlib.contextmanager
def _temporary_xdg_cache_dir():
    key = "XDG_CACHE_HOME"
    with create_temporary_dir() as cache_dir:
        with _updated_env({key: cache_dir}):
            yield


@contextlib.contextmanager
def _updated_env(env_updates):
    original_env = {}
    for key, updated_value in env_updates.iteritems():
        original_env[key] = os.environ.get(key)
    os.environ[key] = updated_value

    try:
        yield
    finally:
        for key, original_value in original_env.iteritems():
            if original_value is None:
                del os.environ[key]
            else:
                os.environ[key] = original_value


WhackNoCachingTests = test_set.create(
    "WhackNoCachingTests",
    functools.partial(_run_test, whack.config.caching_config(enabled=False))
)


WhackCachingTests = test_set.create(
    "WhackCachingTests",
    functools.partial(_run_test, whack.config.caching_config(enabled=True))
)
