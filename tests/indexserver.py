import contextlib
import os

from .httpserver import start_static_http_server
from whack.tempdir import create_temporary_dir
from whack.sources import create_source_tarball
from whack.files import write_file, read_file
from whack.tarballs import create_tarball


@contextlib.contextmanager
def start_index_server():
    with create_temporary_dir() as server_root:
        with start_static_http_server(server_root) as http_server:
            yield IndexServer(http_server)
            
            
class IndexServer(object):
    def __init__(self, http_server):
        self._sources = []
        self._http_server = http_server
        self._root = http_server.root
    
    def index_url(self):
        return self._http_server.static_url("packages.html")
        
    def add_source(self, source_dir):
        source_tarball = create_source_tarball(source_dir, self._root)
        source_filename = os.path.relpath(source_tarball.path, self._root)
        source_url = self._http_server.static_url(source_filename)
        self._sources.append((source_filename, source_url))
        self._generate_index()
        return source_tarball
        
    def add_package(self, package_dir):
        package_name = read_file(os.path.join(package_dir, ".whack-package-name"))
        package_filename = "{0}.whack-package".format(package_name)
        package_tarball_path = os.path.join(self._root, package_filename)
        create_tarball(
            package_tarball_path,
            package_dir,
        )
        package_url = self._http_server.static_url(package_filename)
        self._sources.append((package_filename, package_url))
        self._generate_index()
        
    def _generate_index(self):
        index_path = os.path.join(self._http_server.root, "packages.html")
        write_file(index_path, _html_for_index(self._sources))


def _html_for_index(packages):
    links = [
        '<a href="{0}">{1}</a>'.format(url, name)
        for name, url in packages
    ]
    return """
<!DOCTYPE html>
<html>
  <head>
  </head>
  <body>
    {0}
  </body>
</html>
    """.format("".join(links))
