import os
import subprocess
import json

from nose.tools import istest, assert_equal, assert_raises

from whack.sources import PackageSourceFetcher, PackageSourceNotFound, PackageSource
from whack.tempdir import create_temporary_dir
from whack.files import read_file, write_file, write_files, plain_file


@istest
def can_fetch_package_source_from_source_control():
    with create_temporary_dir() as package_source_dir:
        write_file(os.path.join(package_source_dir, "name"), "Bob")
        _convert_to_git_repo(package_source_dir)
        
        source_fetcher = PackageSourceFetcher()
        repo_uri = "git+file://{0}".format(package_source_dir)
        with source_fetcher.fetch(repo_uri) as package_source:
            assert_equal("Bob", read_file(os.path.join(package_source.path, "name")))


@istest
def can_fetch_package_source_from_local_path():
    with create_temporary_dir() as package_source_dir:
        write_file(os.path.join(package_source_dir, "name"), "Bob")
        
        source_fetcher = PackageSourceFetcher()
        with source_fetcher.fetch(package_source_dir) as package_source:
            assert_equal("Bob", read_file(os.path.join(package_source.path, "name")))


@istest
def error_is_raised_if_package_source_cannot_be_found():
    source_fetcher = PackageSourceFetcher()
    assert_raises(PackageSourceNotFound, lambda: source_fetcher.fetch("nginx"))
    

@istest
def name_is_stored_in_whack_json():
    with create_temporary_dir() as package_source_dir:
        write_files(package_source_dir, [
            plain_file("whack/whack.json", json.dumps({"name": "nginx"})),
        ])
        package_source = PackageSource(package_source_dir)
        assert_equal("nginx", package_source.name())
    

@istest
def name_of_package_source_is_non_if_not_specified_in_whack_json():
    with create_temporary_dir() as package_source_dir:
        write_files(package_source_dir, [
            plain_file("whack/whack.json", json.dumps({})),
        ])
        package_source = PackageSource(package_source_dir)
        assert_equal(None, package_source.name())
    

@istest
def name_of_package_source_is_non_if_whack_json_does_not_exist():
    with create_temporary_dir() as package_source_dir:
        package_source = PackageSource(package_source_dir)
        assert_equal(None, package_source.name())


def _convert_to_git_repo(cwd):
    def _git(command):
        subprocess.check_call(["git"] + command, cwd=cwd)
    _git(["init"])
    _git(["add", "."])
    _git(["commit", "-m", "Initial commit"])
