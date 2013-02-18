import os
import subprocess
import functools
import contextlib

from nose.tools import assert_equal
from nose_test_sets import TestSetBuilder

import whack.operations
import whack.config
import testing
from whack.tempdir import create_temporary_dir
from whack.files import sh_script_description


test_set = TestSetBuilder()
create = test_set.create
test = test_set.add_test


@test
def application_is_installed_by_running_build_script_and_copying_output(ops):
    test_install(
        ops,
        build=testing.HelloWorld.BUILD,
        params={},
        expected_output=testing.HelloWorld.EXPECTED_OUTPUT
    )


@test
def params_are_passed_to_build_script_during_install(ops):
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
        params={"version": "1"},
        expected_output="1\n"
    )


@test
def build_leaves_undeployed_build_in_target_directory(ops):
    with _package_source(testing.HelloWorld.BUILD) as package_source_dir:
        with create_temporary_dir() as target_dir:
            ops.build(package_source_dir, target_dir, params={})
        
            output = subprocess.check_output([os.path.join(target_dir, "hello")])
            assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)
            assert not _is_deployed(target_dir)


@test
def params_are_passed_to_build_script_during_build(ops):
    _TEST_BUILDER_BUILD = r"""#!/bin/sh
set -e
cd $1
echo '#!/bin/sh' >> hello
echo echo ${VERSION} >> hello
chmod +x hello
"""
    
    with _package_source(_TEST_BUILDER_BUILD) as package_source_dir:
        with create_temporary_dir() as target_dir:
            ops.build(package_source_dir, target_dir, params={"version": "1"})
        
            output = subprocess.check_output([os.path.join(target_dir, "hello")])
            assert_equal("1\n", output)


def test_install(ops, build, params, expected_output):
    with _package_source(build) as package_source_dir:
        with create_temporary_dir() as install_dir:
            ops.install(
                package_source_dir,
                install_dir,
                params=params,
            )
            
            output = subprocess.check_output([
                os.path.join(install_dir, "hello")
            ])
            assert_equal(expected_output, output)
            assert _is_deployed(install_dir)


def _run_test(caching, test_func):
    with _temporary_xdg_cache_dir():
        ops = whack.operations.create(caching)
        return test_func(ops)


def _is_deployed(package_dir):
    return os.path.exists(os.path.join(package_dir, ".whack-root-id"))


def _package_source(build):
    return create_temporary_dir([
        sh_script_description("whack/build", build),
    ])


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
