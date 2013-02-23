import os
import json
import tempfile
import uuid
import re

import blah

from .hashes import Hasher
from .files import copy_dir, mkdir_p, copy_file, delete_dir
from .tarballs import extract_tarball, create_tarball
from .indices import read_index


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
    def __init__(self, indices=None):
        if indices is None:
            self._indices = []
        else:
            self._indices = indices
    
    def fetch(self, package, lazy=True):
        fetchers = [IndexFetcher(self._indices), SourceControlFetcher()]
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
        for index_uri in self._indices:
            source = self._fetch_from_index(index_uri, package_name)
            if source is not None:
                return source
        return None
        
    def _fetch_from_index(self, index_uri, package_name):
        index = read_index(index_uri)
        package_source_filename = package_name + _whack_source_uri_suffix
        package_source_entry = index.find_by_name(package_source_filename)
        if package_source_entry is None:
            return None
        else:
            return WhackSourceUriFetcher().fetch(package_source_entry.url)
    

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
            extract_tarball(url, temp_dir, strip_components=1)
            return temp_dir
            
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
            delete_dir(self._package_source_dir)


def _create_temporary_package_source(fetch_package_source_dir):
    temp_dir = _temporary_path()
    try:
        return TemporaryPackageSource(
            fetch_package_source_dir(temp_dir),
            temp_dir
        )
    except:
        delete_dir(temp_dir)
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
        copy_file(source, destination)


class TemporaryPackageSource(object):
    def __init__(self, path, temp_dir):
        self._path = path
        self._temp_dir = temp_dir
    
    def __enter__(self):
        return PackageSource(self._path)
    
    def __exit__(self, *args):
        delete_dir(self._temp_dir)
        

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
    return SourceTarball(full_name, path)


class SourceTarball(object):
    def __init__(self, full_name, path):
        self.full_name = full_name
        self.path = path
