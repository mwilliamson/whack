from nose.tools import istest, assert_equal

from whack.indices import read_index_string
from whack.platform import Platform


@istest
def can_find_source_entry_if_link_text_is_exactly_desired_name():
    index = read_index_string(
        "http://example.com",
        _html('<a href="nginx.tar.gz">nginx.whack-source</a>')
    )
    index_entry = index.find_package_source_by_name("nginx")
    assert_equal("nginx.whack-source", index_entry.name)


@istest
def can_find_source_entry_if_href_is_exactly_desired_name():
    index = read_index_string(
        "http://example.com",
        _html('<a href="nginx.whack-source">n</a>')
    )
    index_entry = index.find_package_source_by_name("nginx")
    assert_equal("n", index_entry.name)


@istest
def can_find_source_entry_if_filename_of_href_is_exactly_desired_name():
    index = read_index_string(
        "http://example.com",
        _html('<a href="source/nginx.whack-source">n</a>')
    )
    index_entry = index.find_package_source_by_name("nginx")
    assert_equal("n", index_entry.name)


@istest
def find_by_name_returns_none_if_entry_cannot_be_found():
    index = read_index_string(
        "http://example.com",
        _html('<a href="nginx">nginx</a>')
    )
    index_entry = index.find_package_source_by_name("nginx")
    assert_equal(None, index_entry)


@istest
def empty_href_attributes_do_not_cause_error():
    index = read_index_string(
        "http://example.com",
        _html('<a href="">n</a>')
    )
    index_entry = index.find_package_source_by_name("nginx")
    assert_equal(None, index_entry)


@istest
def url_is_unchanged_if_href_is_absolute():
    index = read_index_string(
        "http://example.com",
        _html('<a href="http://example.net/nginx.whack-source">nginx.whack-source</a>')
    )
    index_entry = index.find_package_source_by_name("nginx")
    assert_equal("http://example.net/nginx.whack-source", index_entry.url)


@istest
def url_uses_domain_of_index_if_href_is_domain_relative():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">nginx.whack-source</a>')
    )
    index_entry = index.find_package_source_by_name("nginx")
    assert_equal("http://example.com/nginx.whack-source", index_entry.url)


@istest
def can_find_package_by_params_hash_and_platform():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">nginx_linux_x86-64_glibc-2.13_abc.whack-package</a>')
    )
    index_entry = index.find_package(params_hash="abc", platform=_platform)
    assert_equal("http://example.com/nginx.whack-source", index_entry.url)


@istest
def package_entry_is_not_match_if_os_does_not_match():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">nginx_cygwin_x86-64_glibc-2.13_abc.whack-package</a>')
    )
    index_entry = index.find_package(params_hash="abc", platform=_platform)
    assert_equal(None, index_entry)


@istest
def package_entry_is_not_match_if_architecture_does_not_match():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">nginx_linux_i686_glibc-2.13_abc.whack-package</a>')
    )
    index_entry = index.find_package(params_hash="abc", platform=_platform)
    assert_equal(None, index_entry)


@istest
def package_entry_is_not_match_if_libc_does_not_match():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">nginx_linux_x86-64_glibc-2.14_abc.whack-package</a>')
    )
    index_entry = index.find_package(params_hash="abc", platform=_platform)
    assert_equal(None, index_entry)


@istest
def earlier_glibc_can_be_used():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">nginx_linux_x86-64_glibc-2.12_abc.whack-package</a>')
    )
    index_entry = index.find_package(params_hash="abc", platform=_platform)
    assert_equal("nginx_linux_x86-64_glibc-2.12_abc.whack-package", index_entry.name)


@istest
def unrecognised_libc_requires_exact_match():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">nginx_linux_x86-64_xlibc-2.12_abc.whack-package</a>')
    )

    index_entry = index.find_package(params_hash="abc", platform=_platform)
    assert_equal(None, index_entry)


@istest
def package_entries_without_os_name_are_ignored():
    index = read_index_string(
        "http://example.com",
        _html('<a href="/nginx.whack-source">x86-64_xlibc-2.12_abc.whack-package</a>')
    )

    index_entry = index.find_package(params_hash="abc", platform=_platform)
    assert_equal(None, index_entry)


_platform = Platform(
    os_name="linux",
    architecture="x86-64",
    libc="glibc-2.13",
)


def _html(content):
    return """<!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
        {0}
        </body>
        </html>
    """.format(content)
