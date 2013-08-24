def is_local_path(path):
    return (
        path.startswith("/") or
        path.startswith("./") or
        path.startswith("../") or 
        path == "." or
        path == ".."
    )
