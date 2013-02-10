import os
import subprocess
import contextlib

from nose.tools import istest, assert_equal
import mock

import testing
from whack.tempdir import create_temporary_dir
from whack.cli import main
import whack.config


@istest
def application_is_installed_by_running_build_then_install_scripts():
    with create_temporary_dir() as package_source_dir, create_temporary_dir() as install_dir:
        testing.write_package_source(
            package_source_dir,
            {"build": testing.HelloWorld.BUILD},
        )
        
        subprocess.check_call(["whack", "install", package_source_dir, install_dir])
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)


@istest
def params_are_passed_to_install_command_as_dict():
    argv = [
        "whack", "install", "hello=1", "apps/hello",
        "-p", "version=1.2.4", "-p", "pcre_version=8.32"
    ]
    expected_params = {"version": "1.2.4", "pcre_version": "8.32"}
    _test_install_arg_parse(argv, params=expected_params)


@istest
def param_values_can_contain_equals_sign():
    argv = [
        "whack", "install", "hello=1", "apps/hello",
        "-p", "version_range===1.2.4"
    ]
    expected_params = {"version_range": "==1.2.4"}
    _test_install_arg_parse(argv, params=expected_params)
    
@istest
def param_without_equal_sign_has_value_of_empty_string():
    argv = [
        "whack", "install", "hello=1", "apps/hello",
        "-p", "verbose"
    ]
    expected_params = {"verbose": ""}
    _test_install_arg_parse(argv, params=expected_params)


@istest
def http_cache_url_is_passed_along():
    argv = ["whack", "install", "hello", "apps/hello", "--http-cache-url=http://localhost:1234/"]
    caching_config = whack.config.caching_config(enabled=True, http_cache_url="http://localhost:1234/")
    _test_install_arg_parse(argv, caching=caching_config)


@istest
def http_cache_key_is_passed_along():
    argv = [
        "whack", "install", "hello", "apps/hello",
        "--http-cache-url=http://localhost:1234/",
        "--http-cache-key=let-me-in"
    ]
    caching_config = whack.config.caching_config(
        enabled=True,
        http_cache_url="http://localhost:1234/",
        http_cache_key="let-me-in"
    )
    _test_install_arg_parse(argv, caching=caching_config)


def _test_install_arg_parse(argv, env={}, **expected_kwargs):
    operations = mock.Mock()
    with _updated_env(env):
        main(argv, operations)
    
    assert_equal(1, len(operations.install.mock_calls))
    args, kwargs = operations.install.call_args
    for key, value in expected_kwargs.iteritems():
        assert_equal(value, kwargs[key])


@contextlib.contextmanager
def _updated_env(env):
    original_env = os.environ.copy()
    for key, value in env.iteritems():
        os.environ[key] = value
        
    yield
    
    for key in env:
        if key in original_env:
            os.environ[key] = original_env[value]
        else:
            del os.environ[key]
