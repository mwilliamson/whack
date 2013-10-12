import contextlib
import argparse
import os

from nose.tools import istest, assert_equal
import six

import whack.args

env_default = whack.args.env_default(prefix="WHACK")

@istest
def default_value_is_none_if_neither_environment_nor_cli_argument_is_set():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", action=env_default)
    args = parser.parse_args([])
    assert_equal(None, args.title)
    
@istest
def value_from_environment_is_used_if_cli_argument_not_set():
    with _updated_env({"WHACK_TITLE": "Hello!"}):
        parser = argparse.ArgumentParser()
        parser.add_argument("--title", action=env_default)
        args = parser.parse_args([])
    assert_equal("Hello!", args.title)
    
@istest
def value_from_environment_is_ignored_if_cli_argument_is_set():
    with _updated_env({"WHACK_TITLE": "Hello!"}):
        parser = argparse.ArgumentParser()
        parser.add_argument("--title", action=env_default)
        args = parser.parse_args(["--title", "Brilliant"])
    assert_equal("Brilliant", args.title)
    
@istest
def short_option_names_are_ignored_when_generating_environment_name():
    with _updated_env({"WHACK_TITLE": "Hello!"}):
        parser = argparse.ArgumentParser()
        parser.add_argument("-t", "--title", action=env_default)
        args = parser.parse_args([])
    assert_equal("Hello!", args.title)
    
@istest
def additional_long_option_names_are_ignored_when_generating_environment_name():
    with _updated_env({"WHACK_THETITLE": "Hello!"}):
        parser = argparse.ArgumentParser()
        parser.add_argument("--title", "--thetitle", action=env_default)
        args = parser.parse_args([])
    assert_equal(None, args.title)
    
@istest
def hyphens_are_replaced_by_underscores_in_environment_variable_name():
    with _updated_env({"WHACK_THE_TITLE": "Hello!"}):
        parser = argparse.ArgumentParser()
        parser.add_argument("--the-title", action=env_default)
        args = parser.parse_args([])
    assert_equal("Hello!", args.the_title)


class Namespace(object):
    pass


@contextlib.contextmanager
def _updated_env(env):
    original_env = os.environ.copy()
    for key, value in six.iteritems(env):
        os.environ[key] = value
        
    yield
    
    for key in env:
        if key in original_env:
            os.environ[key] = original_env[value]
        else:
            del os.environ[key]
