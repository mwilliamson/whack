from nose.tools import istest, assert_equal

from whack.indices import read_index_string


@istest
def can_find_entry_if_link_text_is_exactly_desired_name():
    index = read_index_string(
        _html('<a href="nginx.tar.gz">nginx.whack-source</a>')
    )
    index_entry = index.find_by_name("nginx.whack-source")
    assert_equal("nginx.tar.gz", index_entry.url)
    assert_equal("nginx.whack-source", index_entry.name)


@istest
def can_find_entry_if_href_is_exactly_desired_name():
    index = read_index_string(
        _html('<a href="nginx.whack-source">n</a>')
    )
    index_entry = index.find_by_name("nginx.whack-source")
    assert_equal("nginx.whack-source", index_entry.url)
    assert_equal("n", index_entry.name)


@istest
def can_find_entry_if_filename_of_href_is_exactly_desired_name():
    index = read_index_string(
        _html('<a href="source/nginx.whack-source">n</a>')
    )
    index_entry = index.find_by_name("nginx.whack-source")
    assert_equal("source/nginx.whack-source", index_entry.url)
    assert_equal("n", index_entry.name)


@istest
def find_by_name_returns_none_if_entry_cannot_be_found():
    index = read_index_string(
        _html('<a href="nginx">nginx</a>')
    )
    index_entry = index.find_by_name("nginx.whack-source")
    assert_equal(None, index_entry)


@istest
def empty_href_attributes_do_not_cause_error():
    index = read_index_string(
        _html('<a href="">n</a>')
    )
    index_entry = index.find_by_name("nginx.whack-source")
    assert_equal(None, index_entry)


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
