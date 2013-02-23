import os
import subprocess
import contextlib

from nose.tools import istest, assert_equal
import spur

from whack import cli
from whack.sources import SourceTarball
from whack.common import PackageNotAvailableError
from . import whack_test


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


def _test_install_arg_parse(argv, **expected_kwargs):
    args = cli.parse_args(argv)
    
    for key, value in expected_kwargs.iteritems():
        assert_equal(value, getattr(args, key))


class CliOperations(object):
    def __init__(self, indices=None, enable_build=True):
        self._indices = indices
        self._enable_build = enable_build
    
    def install(self, package_name, install_dir, params={}):
        self._command("install", package_name, install_dir, params)
        
    def build(self, package_name, target_dir, params={}):
        self._command("build", package_name, target_dir, params)
    
    def deploy(self, package_dir, target_dir=None):
        if target_dir is None:
            self._whack("deploy", package_dir, "--in-place")
        else:
            self._whack("deploy", package_dir, target_dir)
            
    def create_source_tarball(self, source_dir, tarball_dir):
        output = self._whack(
            "create-source-tarball",
            source_dir, tarball_dir,
        ).output
        full_name, path = output.strip().split("\n")
        return SourceTarball(full_name, path)
    
    def _command(self, command_name, package_name, target_dir, params):
        params_args = [
            "-p{0}={1}".format(key, value)
            for key, value in params.iteritems()
        ]
        try:
            self._whack(command_name, package_name, target_dir, *params_args)
        except spur.RunProcessError as process_error:
            # TODO: perhaps we can do something a little less crude?
            if PackageNotAvailableError.__name__ in process_error.stderr_output:
                raise PackageNotAvailableError()
            else:
                raise
        
    def _whack(self, *args):
        local_shell = spur.LocalShell()
        indices_args = [
            "--add-index={0}".format(index)
            for index in (self._indices or [])
        ]
        extra_args = ["--disable-cache"] + indices_args
        if not self._enable_build:
            extra_args.append("--disable-build")
            
        return local_shell.run(["whack"] + list(args) + extra_args)
        


def _run_cli_operations_test(test_func):
    test_func(CliOperations)


WhackCliOperationsTest = whack_test.create(
    "WhackCliOperationsTest",
    _run_cli_operations_test,
)


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
