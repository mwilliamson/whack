import contextlib
import json
import os

from nose.tools import istest, assert_equal

from whack.tempdir import create_temporary_dir
from whack.files import sh_script_description, plain_file, read_file
from whack.sources import PackageSource
from whack.builder import build
from whack.packagerequests import PackageRequest
from whack.errors import FileNotFoundError
    

@istest
def build_uses_params_as_environment_variables_in_build():
    with _package_source("echo $VERSION > $1/version", {}) as package_source:
        with create_temporary_dir() as target_dir:
            build(PackageRequest(package_source, {"version": "42"}), target_dir)
            assert_equal("42\n", read_file(os.path.join(target_dir, "version")))


@istest
def build_uses_default_value_for_param_if_param_not_explicitly_set():
    description = {"defaultParams": {"version": "42"}}
    with _package_source("echo $VERSION > $1/version", description) as package_source:
        with create_temporary_dir() as target_dir:
            build(PackageRequest(package_source, {}), target_dir)
            assert_equal("42\n", read_file(os.path.join(target_dir, "version")))


@istest
def explicit_params_override_default_params():
    description = {"defaultParams": {"version": "42"}}
    with _package_source("echo $VERSION > $1/version", description) as package_source:
        with create_temporary_dir() as target_dir:
            build(PackageRequest(package_source, {"version": "43"}), target_dir)
            assert_equal("43\n", read_file(os.path.join(target_dir, "version")))


@istest
def error_is_raised_if_build_script_is_missing():
    files = [
        plain_file("whack/whack.json", json.dumps({})),
    ]
    with create_temporary_dir(files) as package_source_dir:
        package_source = PackageSource.local(package_source_dir)
        request = PackageRequest(package_source, {})
        with create_temporary_dir() as target_dir:
            assert_raises(
                FileNotFoundError,
                ("whack/build script not found in package source {0}".format(package_source_dir), ),
                lambda: build(request, target_dir),
            )

@contextlib.contextmanager
def _package_source(build_script, description):
    files = [
        plain_file("whack/whack.json", json.dumps(description)),
        sh_script_description("whack/build", build_script),
    ]
    with create_temporary_dir(files) as package_source_dir:
        yield PackageSource.local(package_source_dir)
        

def assert_raises(error_class, args, func):
    try:
        func()
        raise AssertionError("Expected exception {0}".format(error.__name__))
    except error_class as error:
        assert_equal(error.args, args)
