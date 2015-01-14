import os

from nose.tools import istest, assert_equal
from catchy import NoCachingStrategy

from whack.downloads import read_downloads_string, Download, Downloader, DownloadError
from whack import files
from whack.tempdir import create_temporary_dir
from . import httpserver


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


@istest
def downloader_can_download_files_over_http():
    downloader = Downloader(NoCachingStrategy())
    
    with create_temporary_dir() as server_root:
        files.write_file(os.path.join(server_root, "hello"), "Hello there!")
        with httpserver.start_static_http_server(server_root) as http_server:
            with create_temporary_dir() as download_dir:
                download_path = os.path.join(download_dir, "file")
                url = http_server.static_url("hello")
                downloader.download(url, download_path)
                assert_equal("Hello there!", files.read_file(download_path))


@istest
def download_fails_if_http_request_returns_404():
    downloader = Downloader(NoCachingStrategy())
    
    with create_temporary_dir() as server_root:
        with httpserver.start_static_http_server(server_root) as http_server:
            with create_temporary_dir() as download_dir:
                download_path = os.path.join(download_dir, "file")
                url = http_server.static_url("hello")
                try:
                    downloader.download(url, download_path)
                    assert False
                except DownloadError:
                    pass
