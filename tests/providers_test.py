import os
import os.path
import tempfile
import uuid

from nose.tools import istest, assert_equal

from whack.sources import PackageSource
from whack.providers import CachingPackageProvider
from catchy import DirectoryCacher
from whack.files import delete_dir
from whack.packagerequests import PackageRequest
from whack.files import mkdir_p


@istest
class CachingProviderTests(object):
    def __init__(self):
        self._test_dir = tempfile.mkdtemp()
        self._cacher = DirectoryCacher(os.path.join(self._test_dir, "cache"))
        self._underlying_provider = FakeProvider()
        
    def teardown(self):
        delete_dir(self._test_dir)
        
    @istest
    def result_of_build_command_is_reused_when_no_params_are_set(self):
        self._get_package(params={})
        self._get_package(params={})
    
        assert_equal(1, self._number_of_builds())
        
    @istest
    def result_of_build_command_is_reused_when_params_are_the_same(self):
        self._get_package(params={"VERSION": "2.4"})
        self._get_package(params={"VERSION": "2.4"})
    
        assert_equal(1, self._number_of_builds())
        
    @istest
    def result_of_build_command_is_not_reused_when_params_are_not_the_same(self):
        self._get_package(params={"VERSION": "2.4"})
        self._get_package(params={"VERSION": "2.5"})
    
        assert_equal(2, self._number_of_builds())
    
    def _get_package(self, params):
        target_dir = os.path.join(self._test_dir, str(uuid.uuid4()))
        package_source_dir = os.path.join(self._test_dir, str(uuid.uuid4()))
        package_provider = CachingPackageProvider(
            cacher=self._cacher,
            underlying_providers=[self._underlying_provider],
        )
        request = PackageRequest(PackageSource.local(package_source_dir), params)
        package_provider.provide_package(request, target_dir)

    def _number_of_builds(self):
        return len(self._underlying_provider.requests)


class FakeProvider(object):
    def __init__(self):
        self.requests = []
    
    def provide_package(self, package_request, package_dir):
        mkdir_p(package_dir)
        self.requests.append(package_request)
        return True
