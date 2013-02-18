import contextlib
import tempfile
import shutil

from .files import write_files


@contextlib.contextmanager
def create_temporary_dir(file_descriptions=None):
    temporary_dir = tempfile.mkdtemp()
    try:
        if file_descriptions:
            write_files(temporary_dir, file_descriptions)
        yield temporary_dir
    finally:
        shutil.rmtree(temporary_dir)
