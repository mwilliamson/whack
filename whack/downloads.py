import os.path
import hashlib
import urlparse
import re
import urllib

from .tempdir import create_temporary_dir
from .files import mkdir_p, copy_file
from . import local


class DownloadError(Exception):
    pass


class Downloader(object):
    def __init__(self, cacher):
        self._cacher = cacher
    
    def fetch_downloads(self, downloads_file_path, build_env, target_dir):
        downloads_file = _read_downloads_file(downloads_file_path, build_env)
        for download_line in downloads_file:
            self.download(
                download_line.url,
                os.path.join(target_dir, download_line.filename)
            )

    def download(self, url, destination):
        url_hash = hashlib.sha1(url).hexdigest()
        mkdir_p(os.path.dirname(destination))
        cache_result = self._cacher.fetch(url_hash, destination)
        if cache_result.cache_hit:
            return
        else:
            # TODO: writing directly to the cache would be quicker
            # Don't write directly to the destination to avoid any possible
            # modification
            with create_temporary_dir() as temp_dir:
                temp_file_path = os.path.join(temp_dir, url_hash)
                try:
                    local.run(["curl", url, "--output", temp_file_path, "--location", "--fail"])
                except local.RunProcessError as error:
                    if error.return_code == 22: # 404
                        raise DownloadError("File not found: {0}".format(url))
                    else:
                        raise
                    
                copy_file(temp_file_path, destination)
                self._cacher.put(url_hash, temp_file_path)
        

class Download(object):
    def __init__(self, url, filename=None):
        self.url = url
        self.filename = filename or _filename_from_url(url)
        
    def __eq__(self, other):
        return (self.url, self.filename) == (other.url, other.filename)
        
    def __neq__(self, other):
        return not (self == other)
        
    def __repr__(self):
        return "Download({0!r}, {1!r})".format(self.url, self.filename)


def _read_downloads_file(path, build_env):
    if os.path.exists(path):
        first_line = open(path).readline()
        if first_line.startswith("#!"):
            downloads_string = local.run([path], update_env=build_env).output
        else:
            downloads_string = open(path).read()
            
        return read_downloads_string(downloads_string)
    else:
        return []


def read_downloads_string(downloads_string):
    return [
        _read_download_line(line.strip())
        for line in downloads_string.split("\n")
        if line.strip()
    ]

def _read_download_line(line):
    result = re.match("^(\S+)\s+(.+)$", line)
    if result:
        return Download(result.group(1), result.group(2))
    else:
        return Download(line)
    

def _filename_from_url(url):
    return urlparse.urlparse(url).path.rpartition("/")[2]
