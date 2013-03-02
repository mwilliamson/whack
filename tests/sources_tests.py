import os
import subprocess
import json
import contextlib

from nose.tools import istest, assert_equal, assert_raises

from whack.sources import \
    PackageSourceFetcher, PackageSourceNotFound, SourceHashMismatch, \
    PackageSource, create_source_tarball
from whack.tempdir import create_temporary_dir
from whack.files import read_file, write_files, plain_file
from whack.tarballs import create_tarball
from whack.errors import FileNotFoundError
from .httpserver import start_static_http_server
from .indexserver import start_index_server


@istest
def can_fetch_package_source_from_source_control():
    def put_package_source_into_source_control(package_source_dir):
        _convert_to_git_repo(package_source_dir)
        return "git+file://{0}".format(package_source_dir)
        
    _assert_package_source_can_be_written_to_target_dir(
        put_package_source_into_source_control
    )


@istest
def can_fetch_package_source_from_local_dir():
    _assert_package_source_can_be_written_to_target_dir(
        lambda package_source_dir: package_source_dir
    )


@istest
def can_fetch_package_source_from_local_tarball():
    with create_temporary_dir() as temp_dir:
        def create_source(package_source_dir):
            tarball_path = os.path.join(temp_dir, "package.tar.gz")
            return create_tarball(tarball_path, package_source_dir)
        
        _assert_package_source_can_be_written_to_target_dir(create_source)


@istest
def can_fetch_package_source_from_tarball_on_http_server():
    with _temporary_static_server() as server:
        def create_source(package_source_dir):
            tarball_path = os.path.join(server.root, "package.tar.gz")
            create_tarball(tarball_path, package_source_dir)
            return server.static_url("package.tar.gz")
            
        _assert_package_source_can_be_written_to_target_dir(create_source)


@istest
def can_fetch_package_source_from_whack_source_uri():
    with _temporary_static_server() as server:
        def create_source(package_source_dir):
            source_tarball = create_source_tarball(package_source_dir, server.root)
            filename = os.path.relpath(source_tarball.path, server.root)
            return server.static_url(filename)
            
        _assert_package_source_can_be_written_to_target_dir(create_source)


@istest
def error_is_raised_if_hash_is_not_correct():
    with _temporary_static_server() as server:
        with _create_temporary_package_source_dir() as package_source_dir:
            tarball_path = os.path.join(server.root, "package-a452cd.whack-source")
            create_tarball(tarball_path, package_source_dir)
            package_uri = server.static_url("package-a452cd.whack-source")
            
            assert_raises(
                SourceHashMismatch,
                lambda: _fetch_source(package_uri)
            )


@istest
def can_fetch_package_source_using_url_from_html_index():
    with start_index_server() as index_server:
        
        def create_source(package_source_dir):
            source_tarball = index_server.add_source(package_source_dir)
            return source_tarball.full_name
            
        _assert_package_source_can_be_written_to_target_dir(
            create_source,
            indices=[index_server.index_url()]
        )
    

def _assert_package_source_can_be_written_to_target_dir(source_filter, indices=None):
    with _create_temporary_package_source_dir() as package_source_dir:
        package_source_name = source_filter(package_source_dir)
        
        with _fetch_source(package_source_name, indices) as package_source:
            with create_temporary_dir() as target_dir:
                package_source.write_to(target_dir)
                assert_equal(
                    "Bob",
                    read_file(os.path.join(target_dir, "whack/name"))
                )


@contextlib.contextmanager
def _create_temporary_package_source_dir():
    package_source_files = [plain_file("whack/name", "Bob")]
    with create_temporary_dir(package_source_files) as package_source_dir:
        yield package_source_dir


@istest
def writing_package_source_includes_files_specified_in_description():
    with create_temporary_dir() as package_source_dir:
        whack_description = {
            "sourcePaths": ["name"]
        }
        write_files(package_source_dir, [
            plain_file("whack/whack.json", json.dumps(whack_description)),
            plain_file("name", "Bob"),
        ])
        
        with _fetch_source(package_source_dir) as package_source:
            with create_temporary_dir() as target_dir:
                package_source.write_to(target_dir)
                assert_equal(
                    "Bob",
                    read_file(os.path.join(target_dir, "name"))
                )


@istest
def writing_package_source_includes_directories_specified_in_description():
    with create_temporary_dir() as package_source_dir:
        whack_description = {
            "sourcePaths": ["names"]
        }
        write_files(package_source_dir, [
            plain_file("whack/whack.json", json.dumps(whack_description)),
            plain_file("names/bob", "Bob"),
        ])
        
        with _fetch_source(package_source_dir) as package_source:
            with create_temporary_dir() as target_dir:
                package_source.write_to(target_dir)
                assert_equal(
                    "Bob",
                    read_file(os.path.join(target_dir, "names/bob"))
                )


@istest
def writing_source_raises_error_if_file_is_missing():
    with create_temporary_dir() as package_source_dir:
        whack_description = {
            "sourcePaths": ["name"]
        }
        write_files(package_source_dir, [
            plain_file("whack/whack.json", json.dumps(whack_description)),
        ])
        
        with _fetch_source(package_source_dir) as package_source:
            with create_temporary_dir() as target_dir:
                assert_raises(
                    FileNotFoundError,
                    lambda: package_source.write_to(target_dir)
                )


@istest
def error_is_raised_if_package_source_cannot_be_found():
    assert_raises(PackageSourceNotFound, lambda: _fetch_source("nginx/1"))
    

@istest
def name_is_stored_in_whack_json():
    with _source_package_with_description({"name": "nginx"}) as package_source:
        assert_equal("nginx", package_source.name())
    

@istest
def name_of_package_source_is_none_if_not_specified_in_whack_json():
    with _source_package_with_description({}) as package_source:
        assert_equal(None, package_source.name())
    

@istest
def name_of_package_source_is_none_if_whack_json_does_not_exist():
    with create_temporary_dir() as package_source_dir:
        package_source = PackageSource.local(package_source_dir)
        assert_equal(None, package_source.name())
    

@istest
def description_of_package_source_contains_param_slug():
    description = {"name": "nginx", "paramSlug": "$nginx_version"}
    with _source_package_with_description(description) as package_source:
        assert_equal("$nginx_version", package_source.description().param_slug())


@istest
def full_name_of_package_source_is_source_hash_if_name_is_none():
    with _source_package_with_description({}) as package_source:
        assert_equal(package_source.source_hash(), package_source.full_name())


def _convert_to_git_repo(cwd):
    def _git(command):
        subprocess.check_call(["git"] + command, cwd=cwd)
    _git(["init"])
    _git(["add", "."])
    _git(["commit", "-m", "Initial commit"])


def _fetch_source(package_source_uri, indices=None):
    source_fetcher = PackageSourceFetcher(indices=indices)
    return source_fetcher.fetch(package_source_uri)


@contextlib.contextmanager
def _temporary_static_server():
    with create_temporary_dir() as server_root:
        with start_static_http_server(server_root) as server:
            yield server


@contextlib.contextmanager
def _source_package_with_description(description):
    with create_temporary_dir() as package_source_dir:
        write_files(package_source_dir, [
            plain_file("whack/whack.json", json.dumps(description)),
        ])
        yield PackageSource.local(package_source_dir)
