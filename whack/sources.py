import os
import json
import shutil
import tempfile
import uuid
import subprocess

import blah
import requests

from .hashes import Hasher
from .files import copy_dir, mkdir_p, write_file


class PackageSourceNotFound(Exception):
    def __init__(self, package_name):
        message = "Could not find source for package: {0}".format(package_name)
        Exception.__init__(self, message)


class PackageSourceFetcher(object):
    def fetch(self, package):
        if blah.is_source_control_uri(package):
            return self._fetch_package_from_source_control(package)
        elif self._is_http_uri(package) and self._is_tarball(package):
            return self._fetch_package_from_http(package)
        elif self._is_local_path(package):
            if self._is_tarball(package):
                return self._fetch_package_from_tarball(package)
            else:
                return PackageSource(package)
        else:
            raise PackageSourceNotFound(package)
    
    def _fetch_package_from_tarball(self, tarball_path):
        def extract_tarball(destination_dir):
            self._extract_tarball(tarball_path, destination_dir)
            return destination_dir
        
        return self._create_temporary_package_source(extract_tarball)
    
    def _fetch_package_from_source_control(self, source_control_uri):
        def fetch_archive(destination_dir):
            blah.archive(source_control_uri, destination_dir)
            return destination_dir
        
        return self._create_temporary_package_source(fetch_archive)

    def _fetch_package_from_http(self, url):
        def fetch_tarball(temp_dir):
            mkdir_p(temp_dir)
            tarball_path = os.path.join(temp_dir, "package-source.tar.gz")
            response = requests.get(url, stream=True)
            if response.status_code is not 200:
                raise Exception("Status code was: {0}".format(response.status_code))
            with open(tarball_path, "wb") as tarball_file:
                shutil.copyfileobj(response.raw, tarball_file)
            
            package_source_dir = os.path.join(temp_dir, "package-source")
            self._extract_tarball(tarball_path, package_source_dir)
            return package_source_dir
            
        return self._create_temporary_package_source(fetch_tarball)

    def _create_temporary_package_source(self, fetch_package_source_dir):
        temp_dir = _temporary_path()
        try:
            return TemporaryPackageSource(
                fetch_package_source_dir(temp_dir),
                temp_dir
            )
        except:
            shutil.rmtree(temp_dir)
            raise
    
    def _is_http_uri(self, uri):
        return uri.startswith("http://")
    
    def _is_tarball(self, uri):
        return uri.endswith(".tar.gz")
    
    def _extract_tarball(self, tarball_path, destination_dir):
        mkdir_p(destination_dir)
        subprocess.check_call([
            "tar", "xzf", tarball_path,
            "--directory", destination_dir,
            "--strip-components", "1"
        ])
    
    def _is_local_uri(self, uri):
        return "://" not in uri
        
    def _is_local_path(self, path):
        return (
            path.startswith("/") or
            path.startswith("./") or
            path.startswith("../") or 
            path == "." or
            path == ".."
        )


def _temporary_path():
    return os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))


class PackageSource(object):
    def __init__(self, path):
        self._path = path
        self._description = _read_package_description(path)
    
    def name(self):
        return self._description.name()
    
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
