import os
import os.path
import tempfile
import shutil
import functools
import uuid
import contextlib

from nose.tools import istest, assert_equal

from whack.sources import PackageSource
from whack.providers import create_package_provider
from catchy import DirectoryCacher
import testing
from whack.tempdir import create_temporary_dir


def test(func):
    @functools.wraps(func)
    def run_test():
        with TestRunner() as test_runner:
            func(test_runner)
    
    return istest(run_test)


class TestRunner(object):
    def __init__(self):
        self._test_dir = tempfile.mkdtemp()
        self._cacher = DirectoryCacher(os.path.join(self._test_dir, "cache"))
    
    def create_local_package(self, scripts):
        package_dir = self.create_temporary_dir()
        testing.write_package_source(package_dir, scripts)
        return package_dir
    
    def create_temporary_dir(self):
        temp_dir = self.create_temporary_path()
        os.mkdir(temp_dir)
        return temp_dir
        
    def create_temporary_path(self):
        return os.path.join(self._test_dir, str(uuid.uuid4()))

    def build(self, package_source_dir, params):
        build_dir = self.create_temporary_dir()
        package_provider = create_package_provider(cacher=self._cacher)
        package_source = PackageSource(package_source_dir)
        package_provider.provide_package(package_source, params, build_dir)
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        shutil.rmtree(self._test_dir)

    
@test
def result_of_build_command_is_reused_when_no_params_are_set(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.build(package.package_dir, params={})
    test_runner.build(package.package_dir, params={})
    
    assert_equal("building\n", package.read_build_log())
    
    
@test
def result_of_build_command_is_reused_when_params_are_the_same(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.build(package.package_dir, params={"VERSION": "2.4"})
    test_runner.build(package.package_dir, params={"VERSION": "2.4"})
    
    assert_equal("building\n", package.read_build_log())
    
    
@test
def result_of_build_command_is_not_reused_when_params_are_not_the_same(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.build(package.package_dir, params={"VERSION": "2.4"})
    test_runner.build(package.package_dir, params={"VERSION": "2.5"})
    
    assert_equal("building\nbuilding\n", package.read_build_log())
    
    
def _create_logging_package(test_runner):
    build_log = test_runner.create_temporary_path()
    
    _BUILD = r"""#!/bin/sh
echo building >> {0}
""".format(build_log)

    package_dir = test_runner.create_local_package(
        scripts={"build": _BUILD}
    )
    return LoggingPackage(package_dir, build_log)
    
    
class LoggingPackage(object):
    def __init__(self, package_dir, build_log):
        self.package_dir = package_dir
        self._build_log = build_log
        
    def read_build_log(self):
        return open(self._build_log).read()


@contextlib.contextmanager
def _temporary_package_source(build):
    with create_temporary_dir() as package_source_dir:
        testing.write_package_source(package_source_dir, {"build": build})
        yield package_source_dir
