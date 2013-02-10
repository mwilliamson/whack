import os
import contextlib
import json

import blah

from . import downloads
from .tempdir import create_temporary_dir


class PackageSourceFetcher(object):
    def __init__(self, package_source_repo_uris):
        self._package_source_repo_uris = package_source_repo_uris
    
    @contextlib.contextmanager
    def fetch(self, package):
        if blah.is_source_control_uri(package):
            fetch_dir = lambda: self._fetch_package_from_source_control(package)
        elif self._is_local_path(package):
            fetch_dir = lambda: _no_op_context_manager(package)
        else:
            fetch_dir = lambda: self._fetch_package_from_repo(package)
        
        if fetch_dir is None:
            raise RuntimeError("No builders found for package: {0}".format(package))
        else:
            with fetch_dir() as package_source_dir:
                yield PackageSource(package_source_dir)
    
    @contextlib.contextmanager
    def _fetch_package_from_source_control(self, package):
        with create_temporary_dir() as temporary_dir:
            archive_dir = os.path.join(temporary_dir, "archive")
            blah.archive(package, archive_dir)
            yield archive_dir
    
    @contextlib.contextmanager
    def _fetch_package_from_repo(self, package):
        for uri in self._package_source_repo_uris:
            if self._is_local_uri(uri):
                repo_dir = uri
            else:
                repo_dir = downloads.fetch_source_control_uri(uri)
            # FIXME: race condition between this and when we acquire the lock
            package_src_dir = os.path.join(repo_dir, package)
            if os.path.exists(package_src_dir):
                yield package_src_dir
            
    def _is_local_uri(self, uri):
        return "://" not in uri
        
    def _is_local_path(self, path):
        return path.startswith("/") or path.startswith(".")


@contextlib.contextmanager
def _no_op_context_manager(value):
    yield value


class PackageSource(object):
    def __init__(self, path):
        self.path = path

    def template_name(self):
        return _read_package_description(self.path).template_name


_default_template_name = "fixed-root"


def _read_package_description(package_src_dir):
    whack_json_path = os.path.join(package_src_dir, "whack/whack.json")
    if os.path.exists(whack_json_path):
        with open(whack_json_path, "r") as whack_json_file:
            whack_json = json.load(whack_json_file)
        return DictBackedPackageDescription(whack_json)
    else:
        return DefaultPackageDescription()
        
        
class DefaultPackageDescription(object):
    template_name = _default_template_name


class DictBackedPackageDescription(object):
    def __init__(self, values):
        self._values = values
    
    @property
    def template_name(self):
        return self._values.get("template", _default_template_name)
