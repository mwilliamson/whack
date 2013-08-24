def is_local_path(path):
    return (
        path.startswith("/") or
        path.startswith("./") or
        path.startswith("../") or 
        path == "." or
        path == ".."
    )


def is_http_uri(uri):
    return uri.startswith("http://") or uri.startswith("https://")
