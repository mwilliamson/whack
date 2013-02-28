import contextlib
import json
import os

from nose.tools import istest, assert_equal

from whack.tempdir import create_temporary_dir
from whack.files import sh_script_description, plain_file, read_file
from whack.sources import PackageSource
from whack.builder import build
    

@istest
def build_uses_params_as_environment_variables_in_build():
    with _package_source("echo $VERSION > $1/version", {}) as package_source:
        with create_temporary_dir() as target_dir:
            build(package_source, {"version": "42"}, target_dir)
            assert_equal("42\n", read_file(os.path.join(target_dir, "version")))


@contextlib.contextmanager
def _package_source(build_script, description):
    files = [
        plain_file("whack/whack.json", json.dumps(description)),
        sh_script_description("whack/build", build_script),
    ]
    with create_temporary_dir(files) as package_source_dir:
        yield PackageSource(package_source_dir)
        
