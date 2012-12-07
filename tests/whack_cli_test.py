import os
import subprocess

from nose.tools import istest, assert_equal
import mock

import testing
from testing import temporary_dir
from whack.cli import main

@istest
def application_is_installed_by_running_build_then_install_scripts():
    with temporary_dir() as repo_dir, temporary_dir() as install_dir:
        testing.create_test_builder(
            repo_dir,
            testing.HelloWorld.BUILD,
            testing.HelloWorld.INSTALL
        )
        
        subprocess.check_call(["whack", "install", "hello=1", install_dir, "--add-builder-repo", repo_dir])
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal(testing.HelloWorld.EXPECTED_OUTPUT, output)

@istest
def no_builder_repos_are_used_if_add_builder_repo_is_not_set():
    argv = ["whack", "install", "hello=1", "apps/hello"]
    operations = mock.Mock()
    main(argv, operations)
    
    calls = operations.install.mock_calls
    assert_equal(1, len(calls))
    assert_equal([], calls[0].builder_uris)
    
@istest
def all_values_passed_to_add_builder_repo_are_combined_into_builder_uris_arg():
    argv = [
        "whack", "install", "hello=1", "apps/hello",
        "--add-builder-repo", "http://example.com/repo1",
        "--add-builder-repo", "http://example.com/repo2"
    ]
    expected_builder_uris = ["http://example.com/repo1", "http://example.com/repo2"]
    _test_install_arg_parse(argv, builder_uris=expected_builder_uris)

def _test_install_arg_parse(argv, **expected_kwargs):
    operations = mock.Mock()
    main(argv, operations)
    
    assert_equal(1, len(operations.install.mock_calls))
    args, kwargs = operations.install.call_args
    for key, value in expected_kwargs.iteritems():
        assert_equal(value, kwargs[key])
