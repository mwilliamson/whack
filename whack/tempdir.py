import contextlib
import tempfile
import shutil

@contextlib.contextmanager
def create_temporary_dir():
    try:
        build_dir = tempfile.mkdtemp()
        yield build_dir
    finally:
        shutil.rmtree(build_dir)
