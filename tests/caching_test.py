import os
import functools
import socket
import threading
import SocketServer
import BaseHTTPServer
import contextlib
import shutil

from nose.tools import istest, assert_equals, assert_false

from whack.caching import HttpCacher
from whack.tempdir import create_temporary_dir
from whack.tarballs import create_gzipped_tarball_from_dir

_install_id = "c05c2cbd1aa1e3865adba215210a7a82b52ccf90"

def test(func):
    @functools.wraps(func)
    def run_test():
        with create_temporary_dir() as temp_dir:
            cacher_dir = os.path.join(temp_dir, "www-root")
            os.mkdir(cacher_dir)
            with _start_http_server(cacher_dir) as server:
                ip, port = server.server_address
                build_dir = os.path.join(temp_dir, "build")
                base_url = "http://localhost:{0}/".format(port)
                test_runner = TestRunner(build_dir, base_url, cacher_dir)
                func(test_runner)
    
    return istest(run_test)

@test
def fetch_returns_cache_miss_if_http_server_returns_404(test_runner):
    result = test_runner.cacher.fetch(_install_id, test_runner.build_dir)
    assert_equals(False, result.cache_hit)

@test
def fetch_does_not_create_build_dir_if_http_server_returns_404(test_runner):
    test_runner.cacher.fetch(_install_id, test_runner.build_dir)
    assert_false(os.path.exists(test_runner.build_dir))     

@test
def fetch_returns_cache_hit_if_http_server_returns_200(test_runner):
    test_runner.cache_put(_install_id, {"README": "Out of memory and time"})
    result = test_runner.cacher.fetch(_install_id, test_runner.build_dir)
    assert_equals(True, result.cache_hit)
    
@test
def fetch_downloads_and_extracts_tarball_from_http_server(test_runner):
    test_runner.cache_put(_install_id, {"README": "Out of memory and time"})
    result = test_runner.cacher.fetch(_install_id, test_runner.build_dir)
    fetched_file_path = os.path.join(test_runner.build_dir, "README")
    fetched_file_contents = open(fetched_file_path).read()
    assert_equals("Out of memory and time", fetched_file_contents)


@contextlib.contextmanager
def _start_http_server(base_dir):
    class WhackCacheRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            f = self.send_head()
            if f:
                shutil.copyfileobj(f, self.wfile)
                f.close()

        def do_HEAD(self):
            f = self.send_head()
            if f:
                f.close()

        def send_head(self):
            # Wildly assuming no query string nor hash
            path = os.path.join(base_dir, self.path.lstrip("/"))
            if os.path.exists(path):
                try:
                    f = open(path, 'rb')
                except IOError:
                    self.send_error(404, "File not found")
                    return None
                self.send_response(200)
                self.send_header("Content-type", "application/x-gzip")
                fs = os.fstat(f.fileno())
                self.send_header("Content-Length", str(fs[6]))
                self.end_headers()
                return f
            else:
                self.send_error(404, "File not found")
            
    server = SocketServer.TCPServer(("localhost", 0), WhackCacheRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    try:
        yield server
    finally:
        server.shutdown()


class TestRunner(object):
    def __init__(self, build_dir, base_url, cacher_dir):
        self.build_dir = build_dir
        self.cacher = HttpCacher(base_url)
        self._cacher_dir = cacher_dir
        
    def cache_put(self, install_id, files):
        with create_temporary_dir() as temp_dir:
            tarball_dir = os.path.join(temp_dir, install_id)
            os.mkdir(tarball_dir)
            tarball_name = "{0}.tar.gz".format(install_id)
            tarball_path = os.path.join(self._cacher_dir, tarball_name)
            
            for filename, contents in files.iteritems():
                open(os.path.join(tarball_dir, filename), "w").write(contents)
            
            create_gzipped_tarball_from_dir(tarball_dir, tarball_path)
