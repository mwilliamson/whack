import os
import contextlib

import blah

from . import downloads
from .tempdir import create_temporary_dir


class PackageSourceFetcher(object):
    def __init__(self, package_source_repo_uris):
        self._package_source_repo_uris = package_source_repo_uris
    
    def fetch(self, package):
        if blah.is_source_control_uri(package):
            package_src_dir = self._fetch_package_from_source_control(package)
        elif self._is_local_path(package):
            package_src_dir = _no_op_context_manager(package)
        else:
            package_src_dir = self._fetch_package_from_repo(package)
        
        if package_src_dir is None:
            raise RuntimeError("No builders found for package: {0}".format(package))
        else:
            return package_src_dir
    
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
