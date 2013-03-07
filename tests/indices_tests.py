from nose.tools import istest, assert_equal

from whack.indices import read_index_string


@istest
def finding_entries_by_name_uses_link_text():
    index = read_index_string(
        _html('<a href="nginx.tar.gz">nginx.whack-source</a>')
    )
    index_entry = index.find_by_name("nginx.whack-source")
    assert_equal("nginx.tar.gz", index_entry.url)
    assert_equal("nginx.whack-source", index_entry.name)


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
