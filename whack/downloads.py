import os.path
import hashlib
import shutil
import subprocess
import urlparse
import re
import urllib

import blah
import locket


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

        
def fetch_downloads(downloads_file_path, build_env, target_dir):
    downloads_file = _read_downloads_file(downloads_file_path, build_env)
    for download_line in downloads_file:
        download(
            download_line.url,
            os.path.join(target_dir, download_line.filename)
        )


def _read_downloads_file(path, build_env):
    if os.path.exists(path):
        first_line = open(path).readline()
        if first_line.startswith("#!"):
            downloads_string = subprocess.check_output(
                [path],
                env=build_env
            )
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
    

def download(url, destination):
    cache_file = _download_to_cache(url)
    subprocess.check_call(["mkdir", "-p", os.path.dirname(destination)])
    shutil.copyfile(cache_file, destination)

def _download_to_cache(url):
    cache_dir = _whack_cache_dir("downloads/")
    url_hash = hashlib.sha1(url).hexdigest()
    cache_file = os.path.join(cache_dir, url_hash)
    subprocess.check_call(["mkdir", "-p", cache_dir])
    with locket.lock_file("{0}.lock".format(cache_file)):
        if not os.path.exists(cache_file):
            urllib.urlretrieve(url, cache_file)
    return cache_file

def fetch_source_control_uri(uri):
    cache_dir = _whack_cache_dir("repos/")
    repo_hash = hashlib.sha1(uri).hexdigest()
    repo_cache_dir = os.path.join(cache_dir, repo_hash)
    blah.fetch(uri, repo_cache_dir)
    return repo_cache_dir

def _whack_cache_dir(path):
    return os.path.join(os.path.expanduser("~/.cache/whack"), path)

def _filename_from_url(url):
    return urlparse.urlparse(url).path.rpartition("/")[2]
