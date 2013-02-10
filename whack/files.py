import subprocess
import os
import errno


def read_file(path):
    with open(path) as f:
        return f.read()
        

def write_file(path, contents):
    with open(path, "w") as f:
        f.write(contents)


def copy_dir(source, destination):
    # TODO: should be pure Python, but there isn't a stdlib function
    # that allows the destination to already exist
    subprocess.check_call(["cp", "-rT", source, destination])


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if not (error.errno == errno.EEXIST and os.path.isdir(path)):
            raise
