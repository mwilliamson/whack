import threading

import starboard
from wsgiref.simple_server import make_server
from pyramid.config import Configurator

    
def start_static_http_server(root):
    port = starboard.find_local_free_tcp_port()
    config = Configurator()
    config.add_static_view('static', root, cache_max_age=3600)
    app = config.make_wsgi_app()
    
    server = make_server('0.0.0.0', port, app)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return Server(server, server_thread, port)


class Server(object):
    def __init__(self, server, thread, port):
        self.port = port
        self._server = server
        self._thread = thread
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self._server.shutdown()
        self._thread.join()