import os
import subprocess
import shutil

import requests
from bs4 import BeautifulSoup

from . import downloads
from .tempdir import create_temporary_dir
from .naming import name_package
from .common import WHACK_ROOT, PackageNotAvailableError
from .files import mkdir_p
from .builder import build
from .tarballs import extract_tarball


def create_package_provider(cacher, enable_build=True, indices=None):
    if indices is None:
        indices = []
    
    underlying_providers = map(IndexPackageProvider, indices)
    if enable_build:
        underlying_providers.append(BuildingPackageProvider())
    return CachingPackageProvider(cacher, underlying_providers)


class IndexPackageProvider(object):
    def __init__(self, index):
        self._index = index
        
    def provide_package(self, package_source, params, package_dir):
        # TODO: bundle up package_source and params into a PackageRequest
        package_name = name_package(package_source, params)
        # TODO: remove duplication with sources.IndexFetcher
        index_response = requests.get(self._index)
        if index_response.status_code != 200:
            # TODO: should we log and carry on? Definitely shouldn't swallow
            # silently
            raise Exception("Index {0} returned status code {1}".format(
                index, index_response.status_code
            ))
        html_document = BeautifulSoup(index_response.text)
        for link in html_document.find_all("a"):
            if link.get_text().strip() == "{0}.whack-package".format(package_name):
                url = link.get("href")
                self._fetch_and_extract(url, package_dir)
                return True
        return None
        
    def _fetch_and_extract(self, url, package_dir):
        # TODO: remove duplication with sources module
        with create_temporary_dir() as temp_dir:
            tarball_path = os.path.join(temp_dir, "package.tar.gz")
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise Exception("Status code was: {0}".format(response.status_code))
            with open(tarball_path, "wb") as tarball_file:
                shutil.copyfileobj(response.raw, tarball_file)
            
            # TODO: verify hash
            extract_tarball(tarball_path, package_dir, strip_components=1)
    

class BuildingPackageProvider(object):
    def provide_package(self, package_src, params, package_dir):
        build(package_src, params, package_dir)
        return True


class CachingPackageProvider(object):
    def __init__(self, cacher, underlying_providers):
        self._cacher = cacher
        self._underlying_providers = underlying_providers
    
    def provide_package(self, package_source, params, package_dir):
        package_name = name_package(package_source, params)
        result = self._cacher.fetch(package_name, package_dir)
        
        if not result.cache_hit:
            self._provide_package_without_cache(package_source, params, package_dir)
            self._cacher.put(package_name, package_dir)
            
    def _provide_package_without_cache(self, package_source, params, package_dir):
        for underlying_provider in self._underlying_providers:
            package = underlying_provider.provide_package(package_source, params, package_dir)
            if package is not None:
                return package
        raise PackageNotAvailableError()
