from nose.tools import istest, assert_equal

from whack.downloads import read_downloads_string, Download


@istest
def filename_of_download_uses_url_if_not_explicitly_set():
    download = Download("http://nginx.org/download/nginx-1.2.6.tar.gz")
    assert_equal("nginx-1.2.6.tar.gz", download.filename)

@istest
def empty_plain_text_file_has_no_downloads():
    assert_equal([], read_downloads_string(""))
    
@istest
def blank_lines_in_downloads_file_are_ignored():
    assert_equal([], read_downloads_string("\n\n   \n\n"))
    
@istest
def each_line_of_downloads_file_is_url_of_download():
    assert_equal(
        [Download("http://nginx.org/download/nginx-1.2.6.tar.gz")],
        read_downloads_string("http://nginx.org/download/nginx-1.2.6.tar.gz")
    )

@istest
def filename_can_be_explicitly_set_after_url():
    assert_equal(
        [Download("http://nginx.org/download/nginx-1.2.6.tar.gz", "nginx.tar.gz")],
        read_downloads_string("http://nginx.org/download/nginx-1.2.6.tar.gz nginx.tar.gz")
    )
