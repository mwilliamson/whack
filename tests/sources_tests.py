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
from .httpserver import start_static_http_server


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
            return "http://localhost:{0}/static/package.tar.gz".format(server.port)
            
        _assert_package_source_can_be_written_to_target_dir(create_source)


@istest
def source_hash_does_not_require_download_when_using_whack_source_uris():
    package_source_name = "whack-source+http://localhost:{0}/package-35eskc8kcp84pv8f92l0c8749gac0ul0.tar.gz"
    with _fetch_source(package_source_name) as package_source:
        assert_equal("35eskc8kcp84pv8f92l0c8749gac0ul0", package_source.source_hash())


@istest
def can_fetch_package_source_from_whack_source_uri():
    with _temporary_static_server() as server:
        def create_source(package_source_dir):
            source_tarball = create_source_tarball(package_source_dir, server.root)
            return "whack-source+http://localhost:{0}/static/{1}".format(
                server.port,
                source_tarball.uri.split("/")[-1],
            )
            
        _assert_package_source_can_be_written_to_target_dir(create_source)


@istest
def error_is_raised_if_hash_is_not_correct():
    with _temporary_static_server() as server:
        package_source_files = [plain_file("whack/name", "Bob")]
        with create_temporary_dir(package_source_files) as package_source_dir:
            tarball_path = os.path.join(server.root, "package-a452cd.tar.gz")
            create_tarball(tarball_path, package_source_dir)
            package_uri = "whack-source+http://localhost:{0}/static/package-a452cd.tar.gz".format(server.port)
            
            with _fetch_source(package_uri) as package_source:
                with create_temporary_dir() as target_dir:
                    assert_raises(SourceHashMismatch, lambda: package_source.write_to(target_dir))
    

def _assert_package_source_can_be_written_to_target_dir(source_filter):
    package_source_files = [plain_file("whack/name", "Bob")]
    with create_temporary_dir(package_source_files) as package_source_dir:
        package_source_name = source_filter(package_source_dir)
        
        with _fetch_source(package_source_name) as package_source:
            with create_temporary_dir() as target_dir:
                package_source.write_to(target_dir)
                assert_equal(
                    "Bob",
                    read_file(os.path.join(target_dir, "whack/name"))
                )


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
def error_is_raised_if_package_source_cannot_be_found():
    assert_raises(PackageSourceNotFound, lambda: _fetch_source("nginx"))
    

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


def _fetch_source(package_source_uri):
    source_fetcher = PackageSourceFetcher()
    return source_fetcher.fetch(package_source_uri)


@contextlib.contextmanager
def _temporary_static_server():
    with create_temporary_dir() as server_root:
        with start_static_http_server(server_root) as server:
            yield server
