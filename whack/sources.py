import os
import json
import shutil
import tempfile
import uuid

import blah


class PackageSourceNotFound(Exception):
    def __init__(self, package_name):
        message = "Could not find source for package: {0}".format(package_name)
        Exception.__init__(self, message)


class PackageSourceFetcher(object):
    def fetch(self, package):
        if blah.is_source_control_uri(package):
            return self._fetch_package_from_source_control(package)
        elif self._is_local_path(package):
            return PackageSource(package)
        else:
            raise PackageSourceNotFound(package)
    
    def _fetch_package_from_source_control(self, package):
        package_source_dir = _temporary_path()
        try:
            blah.archive(package, package_source_dir)
            return TemporaryPackageSource(package_source_dir)
        except:
            shutil.rmtree(package_source_dir)
            raise
            
    def _is_local_uri(self, uri):
        return "://" not in uri
        
    def _is_local_path(self, path):
        return path.startswith("/") or path.startswith(".")


def _temporary_path():
    return os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))


class PackageSource(object):
    def __init__(self, path):
        self.path = path
        self._description = _read_package_description(path)
    
    def name(self):
        return self._description.name()
        
    def source_paths(self):
        return ["whack"]
    
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass


class TemporaryPackageSource(object):
    def __init__(self, path):
        self.path = path
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        shutil.rmtree(self.path)
        

def _read_package_description(package_src_dir):
    whack_json_path = os.path.join(package_src_dir, "whack/whack.json")
    if os.path.exists(whack_json_path):
        with open(whack_json_path, "r") as whack_json_file:
            whack_json = json.load(whack_json_file)
        return DictBackedPackageDescription(whack_json)
    else:
        return DefaultPackageDescription()
        
        
class DefaultPackageDescription(object):
    def name(self):
        return None


class DictBackedPackageDescription(object):
    def __init__(self, values):
        self._values = values
        
    def name(self):
        return self._values.get("name", None)
