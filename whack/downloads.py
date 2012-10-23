import os.path
import hashlib
import shutil
import subprocess
import urlparse

import blah

from whack.filelock import FileLock

def download(url, destination):
    cache_file = download_to_cache(url)
    subprocess.check_call(["mkdir", "-p", os.path.dirname(destination)])
    shutil.copyfile(cache_file, destination)
    
def download_to_dir(url, destination_dir):
    download(url, os.path.join(destination_dir, _filename_from_url(url)))

def download_to_cache(url):
    cache_dir = _whack_cache_dir("downloads/")
    url_hash = hashlib.sha1(url).hexdigest()
    cache_file = os.path.join(cache_dir, url_hash)
    subprocess.check_call(["mkdir", "-p", cache_dir])
    with FileLock(cache_file):
        if not os.path.exists(cache_file):
            subprocess.check_call(["curl", url, "--create-dirs", "-o", cache_file])
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
