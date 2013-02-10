import os
import subprocess

from nose.tools import istest, assert_equal

from whack.sources import PackageSourceFetcher
from whack.tempdir import create_temporary_dir
from whack.files import read_file, write_file


@istest
def can_fetch_package_source_from_source_control():
    with create_temporary_dir() as package_source_dir:
        write_file(os.path.join(package_source_dir, "name"), "Bob")
        _convert_to_git_repo(package_source_dir)
        
        source_fetcher = PackageSourceFetcher([])
        repo_uri = "git+file://{0}".format(package_source_dir)
        with source_fetcher.fetch(repo_uri) as package_source:
            assert_equal("Bob", read_file(os.path.join(package_source.path, "name")))


@istest
def can_fetch_package_source_from_local_path():
    with create_temporary_dir() as package_source_dir:
        write_file(os.path.join(package_source_dir, "name"), "Bob")
        
        source_fetcher = PackageSourceFetcher([])
        with source_fetcher.fetch(package_source_dir) as package_source:
            assert_equal("Bob", read_file(os.path.join(package_source.path, "name")))
    


def _convert_to_git_repo(cwd):
    def _git(command):
        subprocess.check_call(["git"] + command, cwd=cwd)
    _git(["init"])
    _git(["add", "."])
    _git(["commit", "-m", "Initial commit"])
