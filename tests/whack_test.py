import os
import subprocess
import functools
import contextlib

from nose.tools import assert_equal
from nose_test_sets import TestSetBuilder

from whack.common import WHACK_ROOT
import whack.operations
import testing
from whack.tempdir import create_temporary_dir
from whack.files import write_file, sh_script_description, plain_file
from whack.sources import create_source_tarball
from .httpserver import start_static_http_server


test_set = TestSetBuilder()
create = test_set.create
test = test_set.add_test


def test_with_operations(test_func):
    @test
    @functools.wraps(test_func)
    def run_test(create_operations):
        operations = create_operations()
        return test_func(operations)
    
    return run_test


@test_with_operations
def application_is_installed_by_running_build_script_and_copying_output(ops):
    test_install(
        ops,
        build=testing.HelloWorld.BUILD,
        params={},
        expected_output=testing.HelloWorld.EXPECTED_OUTPUT
    )


@test_with_operations
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


@test_with_operations
def build_leaves_undeployed_build_in_target_directory(ops):
    with _package_source(testing.HelloWorld.BUILD) as package_source_dir:
        with create_temporary_dir() as target_dir:
            ops.build(package_source_dir, target_dir, params={})
        
            output = subprocess.check_output([os.path.join(target_dir, "hello")])
            assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)
            assert not _is_deployed(target_dir)


@test_with_operations
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


@test_with_operations
def built_package_can_be_deployed_to_different_directory(ops):
    package_files = [
        plain_file("message", "Hello there"),
        sh_script_description(".bin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ]
    
    with create_temporary_dir(package_files) as package_dir:
        with create_temporary_dir() as install_dir:
            ops.deploy(package_dir, install_dir)
            output = subprocess.check_output([os.path.join(install_dir, "bin/hello")])
            assert_equal("Hello there", output)
            assert _is_deployed(install_dir)
            assert not _is_deployed(package_dir)
    


@test_with_operations
def directory_can_be_deployed_in_place(ops):
    package_files = [
        plain_file("message", "Hello there"),
        sh_script_description(".bin/hello", "cat {0}/message".format(WHACK_ROOT)),
    ]
    
    with create_temporary_dir(package_files) as package_dir:
        ops.deploy(package_dir)
        output = subprocess.check_output([os.path.join(package_dir, "bin/hello")])
        assert_equal("Hello there", output)
        assert _is_deployed(package_dir)


@test_with_operations
def source_tarballs_created_by_whack_can_be_built(ops):
    with _package_source(testing.HelloWorld.BUILD) as package_source_dir:
        with create_temporary_dir() as tarball_dir:
            source_tarball = ops.create_source_tarball(
                package_source_dir,
                tarball_dir
            )
            with create_temporary_dir() as target_dir:
                ops.build(source_tarball.path, target_dir, params={})
            
                output = subprocess.check_output([os.path.join(target_dir, "hello")])
                assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)


@test
def packages_can_be_installed_from_html_index(create_operations):
    with _package_source(testing.HelloWorld.BUILD) as package_source_dir:
        with _temporary_static_server() as server:
            index_url = server.static_url("packages.html")
            index_path = os.path.join(server.root, "packages.html")
            
            source_tarball = create_source_tarball(
                package_source_dir,
                server.root
            )
            
            source_filename = os.path.relpath(source_tarball.path, server.root)
            source_full_name = source_tarball.full_name
            source_url = server.static_url(source_filename)
            write_file(index_path, _html_for_index([
                (source_filename, source_url)
            ]))
                
            with create_temporary_dir() as target_dir:
                operations = create_operations(indices=[index_url])
                operations.build(source_full_name, target_dir, params={})
            
                output = subprocess.check_output([os.path.join(target_dir, "hello")])
                assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)


@contextlib.contextmanager
def _temporary_static_server():
    with create_temporary_dir() as server_root:
        with start_static_http_server(server_root) as server:
            yield server


# TODO: remove duplication with sources_test
def _html_for_index(packages):
    links = [
        '<a href="{0}">{1}</a>'.format(url, name)
        for name, url in packages
    ]
    return """
<!DOCTYPE html>
<html>
  <head>
  </head>
  <body>
    {0}
  </body>
</html>
    """.format("".join(links))
    

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


def _run_test(test_func, caching_enabled):
    with _temporary_xdg_cache_dir():
        create_operations = functools.partial(
            whack.operations.create,
            caching_enabled
        )
        return test_func(create_operations)


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
    functools.partial(_run_test, caching_enabled=False)
)


WhackCachingTests = test_set.create(
    "WhackCachingTests",
    functools.partial(_run_test, caching_enabled=True)
)
