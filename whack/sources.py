import os
import json
import shutil
import tempfile
import uuid
import re

from bs4 import BeautifulSoup
import blah
import requests

from .hashes import Hasher
from .files import copy_dir, mkdir_p
from .tarballs import extract_tarball, create_tarball


_whack_source_uri_suffix = ".whack-source"


class PackageSourceNotFound(Exception):
    def __init__(self, package_name):
        message = "Could not find source for package: {0}".format(package_name)
        Exception.__init__(self, message)
        
        
class SourceHashMismatch(Exception):
    def __init__(self, expected_hash, actual_hash):
        message = "Expected hash {0} but was {1}".format(
            expected_hash,
            actual_hash
        )
        Exception.__init__(self, message)


class PackageSourceFetcher(object):
    def fetch(self, package, indices=None, lazy=True):
        if indices is None:
            indices = []
        
        fetchers = [IndexFetcher(indices), SourceControlFetcher()]
        if lazy:
            fetchers.append(WhackSourceUriFetcher())
        fetchers += [
            HttpFetcher(),
            LocalPathFetcher(),
        ]
        for fetcher in fetchers:
            package_source = self._fetch_with_fetcher(fetcher, package)
            if package_source is not None:
                return package_source
                
        raise PackageSourceNotFound(package)
        
    def _fetch_with_fetcher(self, fetcher, package):
        if fetcher.can_fetch(package):
            return fetcher.fetch(package)
        else:
            return None


class IndexFetcher(object):
    def __init__(self, indices):
        self._indices = indices
    
    def can_fetch(self, package):
        return re.match(r"^[a-z0-9\-]+$", package)
        
    def fetch(self, package_name):
        for index in self._indices:
            source = self._fetch_from_index(index, package_name)
            if source is not None:
                return source
        return None
        
    def _fetch_from_index(self, index, package_name):
        index_response = requests.get(index)
        if index_response.status_code != 200:
            # TODO: should we log and carry on? Definitely shouldn't swallow
            # silently
            raise Exception("Index {0} returned status code {1}".format(
                index, index_response.status_code
            ))
        html_document = BeautifulSoup(index_response.text)
        for link in html_document.find_all("a"):
            if link.get_text().strip() == "{0}{1}".format(package_name, _whack_source_uri_suffix):
                source_url = link.get("href")
                return WhackSourceUriFetcher().fetch(source_url)
        return None
    

class SourceControlFetcher(object):
    def can_fetch(self, package):
        return blah.is_source_control_uri(package)
        
    def fetch(self, source_control_uri):
        def fetch_archive(destination_dir):
            blah.archive(source_control_uri, destination_dir)
            return destination_dir
        
        return _create_temporary_package_source(fetch_archive)
        
        
class LocalPathFetcher(object):
    def can_fetch(self, package):
        return (
            package.startswith("/") or
            package.startswith("./") or
            package.startswith("../") or 
            package == "." or
            package == ".."
        )
        
    def fetch(self, path):
        if os.path.isfile(path):
            return self._fetch_package_from_tarball(path)
        else:
            return PackageSource(path)
    
    def _fetch_package_from_tarball(self, tarball_path):
        def fetch_directory(destination_dir):
            extract_tarball(tarball_path, destination_dir, strip_components=1)
            return destination_dir
        
        return _create_temporary_package_source(fetch_directory)
        

class HttpFetcher(object):
    def can_fetch(self, package):
        return package.startswith("http://")
        
    def fetch(self, url):
        def fetch_directory(temp_dir):
            mkdir_p(temp_dir)
            tarball_path = os.path.join(temp_dir, "package-source.tar.gz")
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise Exception("Status code was: {0}".format(response.status_code))
            with open(tarball_path, "wb") as tarball_file:
                shutil.copyfileobj(response.raw, tarball_file)
            
            package_source_dir = os.path.join(temp_dir, "package-source")
            extract_tarball(tarball_path, package_source_dir, strip_components=1)
            return package_source_dir
            
        return _create_temporary_package_source(fetch_directory)


class WhackSourceUriFetcher(object):
    def can_fetch(self, package):
        return package.endswith(_whack_source_uri_suffix)
        
    def fetch(self, uri):
        result = re.search(r"/(?:([^./]*)-)?([^./]*)\..*$", uri)
        name = result.group(1)
        source_hash = result.group(2)
        return RemotePackageSource(name, source_hash, uri)


class RemotePackageSource(object):
    def __init__(self, name, source_hash, uri):
        self._name = name
        self._source_hash = source_hash
        self._uri = uri
        self._package_source_dir = None
    
    def name(self):
        return self._name
    
    def source_hash(self):
        return self._source_hash
    
    def write_to(self, target_dir):
        self._fetch_package_source().write_to(target_dir)
    
    def _fetch_package_source(self):
        if self._package_source_dir is None:
            self._package_source_dir = _temporary_path()
            mkdir_p(self._package_source_dir)
            fetcher = PackageSourceFetcher()
            with fetcher.fetch(self._uri, lazy=False) as package_source:
                self._verify_hash(package_source)
                
                package_source.write_to(self._package_source_dir)
            
        return PackageSource(self._package_source_dir)
    
    def _verify_hash(self, package_source):
        expected_hash = self._source_hash
        actual_hash = package_source.source_hash()
        if expected_hash != actual_hash:
            raise SourceHashMismatch(expected_hash, actual_hash)
    
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        if self._package_source_dir is not None:
            if os.path.exists(self._package_source_dir):
                shutil.rmtree(self._package_source_dir)


def _create_temporary_package_source(fetch_package_source_dir):
    temp_dir = _temporary_path()
    try:
        return TemporaryPackageSource(
            fetch_package_source_dir(temp_dir),
            temp_dir
        )
    except:
        shutil.rmtree(temp_dir)
        raise


def _temporary_path():
    return os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))


def _is_tarball(path):
    return path.endswith(".tar.gz")


class PackageSource(object):
    def __init__(self, path):
        self._path = path
        self._description = _read_package_description(path)
    
    def name(self):
        return self._description.name()
        
    def full_name(self):
        name = self.name()
        source_hash = self.source_hash()
        if name is None:
            return source_hash
        else:
            return "{0}-{1}".format(name, source_hash)
    
    def source_hash(self):
        hasher = Hasher()
        for source_path in self._source_paths():
            absolute_source_path = os.path.join(self._path, source_path)
            hasher.update_with_dir(absolute_source_path)
        return hasher.ascii_digest()
    
    def write_to(self, target_dir):
        for source_dir in self._source_paths():
            target_sub_dir = os.path.join(target_dir, source_dir)
            _copy_dir_or_file(os.path.join(self._path, source_dir), target_sub_dir)
    
    def _source_paths(self):
        return ["whack"] + self._description.source_paths()
    
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass


def _copy_dir_or_file(source, destination):
    if os.path.isdir(source):
        copy_dir(source, destination)
    else:
        shutil.copyfile(source, destination)


class TemporaryPackageSource(object):
    def __init__(self, path, temp_dir):
        self._path = path
        self._temp_dir = temp_dir
    
    def __enter__(self):
        return PackageSource(self._path)
    
    def __exit__(self, *args):
        shutil.rmtree(self._temp_dir)
        

def _read_package_description(package_src_dir):
    whack_json_path = os.path.join(package_src_dir, "whack/whack.json")
    if os.path.exists(whack_json_path):
        with open(whack_json_path, "r") as whack_json_file:
            whack_json = json.load(whack_json_file)
    else:
        whack_json = {}
    return DictBackedPackageDescription(whack_json)
        
        
class DictBackedPackageDescription(object):
    def __init__(self, values):
        self._values = values
        
    def name(self):
        return self._values.get("name", None)
        
    def source_paths(self):
        return self._values.get("sourcePaths", [])


def create_source_tarball(source_dir, tarball_dir):
    package_source = PackageSource(source_dir)
    full_name = package_source.full_name()
    filename = "{0}{1}".format(full_name, _whack_source_uri_suffix)
    path = os.path.join(tarball_dir, filename)
    create_tarball(path, source_dir)
    return SourceTarball(path)


class SourceTarball(object):
    def __init__(self, path):
        self.path = path
