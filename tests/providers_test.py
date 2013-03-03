import os
import os.path
import tempfile
import uuid

from nose.tools import istest, assert_equal

from whack.sources import PackageSource
from whack.providers import CachingPackageProvider, BuildingPackageProvider
from catchy import DirectoryCacher
import testing
from whack.files import read_file, delete_dir
from whack.packagerequests import PackageRequest
from whack.builder import Builder
from whack.downloads import Downloader


@istest
class CachingProviderTests(object):
    def __init__(self):
        self._test_dir = tempfile.mkdtemp()
        self._cacher = DirectoryCacher(os.path.join(self._test_dir, "cache"))
        
        self._build_log_path = os.path.join(self._test_dir, "build.log")
        build_script = (
            "#!/bin/sh\n" +
            "echo building >> {0}".format(self._build_log_path)
        )
        
        self._package_source_dir = os.path.join(self._test_dir, "package-source")
        testing.write_package_source(
            self._package_source_dir,
            {"build": build_script}
        )
        
    def teardown(self):
        delete_dir(self._test_dir)
        
    @istest
    def result_of_build_command_is_reused_when_no_params_are_set(self):
        self._get_package(params={})
        self._get_package(params={})
    
        assert_equal("building\n", self._read_build_log())
        
    @istest
    def result_of_build_command_is_reused_when_params_are_the_same(self):
        self._get_package(params={"VERSION": "2.4"})
        self._get_package(params={"VERSION": "2.4"})
    
        assert_equal("building\n", self._read_build_log())
        
    @istest
    def result_of_build_command_is_not_reused_when_params_are_not_the_same(self):
        self._get_package(params={"VERSION": "2.4"})
        self._get_package(params={"VERSION": "2.5"})
    
        assert_equal("building\nbuilding\n", self._read_build_log())
    
    def _get_package(self, params):
        target_dir = os.path.join(self._test_dir, str(uuid.uuid4()))
        builder = Builder(downloader=Downloader(None))
        package_provider = CachingPackageProvider(
            cacher=self._cacher,
            underlying_providers=[BuildingPackageProvider(builder)],
        )
        package_source = PackageSource.local(self._package_source_dir)
        request = PackageRequest(package_source, params)
        package_provider.provide_package(request, target_dir)
        
    def _read_build_log(self):
        return read_file(self._build_log_path)
