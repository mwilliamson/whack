import os
import json
import tempfile
import uuid
import re
import errno

import mayo

from .hashes import Hasher
from .files import copy_dir, copy_file, delete_dir
from .tarballs import extract_tarball, create_tarball
from .indices import read_index
from .errors import FileNotFoundError, WhackUserError
from .tempdir import create_temporary_dir
from .uris import is_local_path, is_http_uri
from . import slugs
from .common import SOURCE_URI_SUFFIX


class PackageSourceNotFound(WhackUserError):
    def __init__(self, source_name):
        message = "Could not find package source: {0}".format(source_name)
        Exception.__init__(self, message)
        
        
class SourceHashMismatch(WhackUserError):
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
    
    def fetch(self, source_name):
        index_fetchers = map(IndexFetcher, self._indices)
        fetchers = index_fetchers + [
            SourceControlFetcher(),
            HttpFetcher(),
            LocalPathFetcher(),
        ]
        for fetcher in fetchers:
            package_source = self._fetch_with_fetcher(fetcher, source_name)
            if package_source is not None:
                try:
                    self._verify(source_name, package_source)
                    return package_source
                except:
                    package_source.__exit__()
                    raise
        raise PackageSourceNotFound(source_name)
        
    def _fetch_with_fetcher(self, fetcher, source_name):
        if fetcher.can_fetch(source_name):
            return fetcher.fetch(source_name)
        else:
            return None
            
    def _verify(self, source_name, package_source):
        if source_name.endswith(SOURCE_URI_SUFFIX):
            full_name = source_name[:-len(SOURCE_URI_SUFFIX)]
            expected_hash = slugs.split(full_name)[-1]
            actual_hash = package_source.source_hash()
            if expected_hash != actual_hash:
                raise SourceHashMismatch(expected_hash, actual_hash)


class IndexFetcher(object):
    def __init__(self, index_uri):
        self._index_uri = index_uri
    
    def can_fetch(self, source_name):
        return re.match(r"^[a-z0-9\-_]+$", source_name)
        
    def fetch(self, source_name):
        index = read_index(self._index_uri)
        package_source_entry = index.find_package_source_by_name(source_name)
        if package_source_entry is None:
            return None
        else:
            return HttpFetcher().fetch(package_source_entry.url)
    

class SourceControlFetcher(object):
    def can_fetch(self, source_name):
        return mayo.is_source_control_uri(source_name)
        
    def fetch(self, source_name):
        def fetch_archive(destination_dir):
            mayo.archive(source_name, destination_dir)
        
        return _create_temporary_package_source(source_name, fetch_archive)
        
        
class LocalPathFetcher(object):
    def can_fetch(self, source_name):
        return is_local_path(source_name)
        
    def fetch(self, source_name):
        if os.path.isfile(source_name):
            return self._fetch_package_from_tarball(source_name)
        else:
            return PackageSource.local(source_name)
    
    def _fetch_package_from_tarball(self, tarball_path):
        def fetch_directory(destination_dir):
            extract_tarball(tarball_path, destination_dir, strip_components=1)
            return destination_dir
        
        return _create_temporary_package_source(tarball_path, fetch_directory)
        

class HttpFetcher(object):
    def can_fetch(self, source_name):
        return is_http_uri(source_name)
        
    def fetch(self, source_name):
        def fetch_directory(temp_dir):
            extract_tarball(source_name, temp_dir, strip_components=1)
            
        return _create_temporary_package_source(source_name, fetch_directory)


def _create_temporary_package_source(uri, fetch_package_source_dir):
    temp_dir = _temporary_path()
    try:
        fetch_package_source_dir(temp_dir)
        return PackageSource(temp_dir, uri, is_temp=True)
    except:
        delete_dir(temp_dir)
        raise


def _temporary_path():
    return os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))


def _is_tarball(path):
    return path.endswith(".tar.gz")


class PackageSource(object):
    @staticmethod
    def local(path):
        return PackageSource(path, path, is_temp=False)
    
    def __init__(self, path, uri, is_temp):
        self.path = path
        self.uri = uri
        self._description = _read_package_description(path)
        self._is_temp = is_temp
    
    def name(self):
        return self._description.name()
    
    def full_name(self):
        name = self.name()
        source_hash = self.source_hash()
        return slugs.join([name, source_hash])
    
    def source_hash(self):
        hasher = Hasher()
        for source_path in self._source_paths():
            absolute_source_path = os.path.join(self.path, source_path)
            hasher.update_with_dir(absolute_source_path)
        return hasher.ascii_digest()
    
    def write_to(self, target_dir):
        for source_dir in self._source_paths():
            target_sub_dir = os.path.join(target_dir, source_dir)
            try:
                _copy_dir_or_file(
                    os.path.join(self.path, source_dir),
                    target_sub_dir
                )
            except IOError as error:
                if error.errno == errno.ENOENT:
                    raise FileNotFoundError()
                else:
                    raise error
    
    def description(self):
        return self._description
    
    def _source_paths(self):
        return self._description.source_paths()
    
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        if self._is_temp:
            delete_dir(self.path)


def _copy_dir_or_file(source, destination):
    if os.path.isdir(source):
        copy_dir(source, destination)
    else:
        copy_file(source, destination)
        

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
        return self._values.get("name", "unknown")
        
    def param_slug(self):
        return self._values.get("paramSlug", None)
        
    def source_paths(self):
        return self._values.get("sourcePaths", ["whack"])
        
    def default_params(self):
        return self._values.get("defaultParams", {})
        
    def test_command(self):
        return self._values.get("test", None)


def create_source_tarball(package_source, tarball_dir):
    with create_temporary_dir() as source_dir:
        package_source.write_to(source_dir)
        full_name = package_source.full_name()
        filename = "{0}{1}".format(full_name, SOURCE_URI_SUFFIX)
        path = os.path.join(tarball_dir, filename)
        create_tarball(path, source_dir)
        return SourceTarball(full_name, path)


class SourceTarball(object):
    def __init__(self, full_name, path):
        self.full_name = full_name
        self.path = path
