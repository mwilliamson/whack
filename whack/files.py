import os
import errno
import shutil

from . import local


def read_file(path):
    with open(path) as f:
        return f.read()
        

def write_file(path, contents):
    with open(path, "w") as f:
        f.write(contents)


copy_file = shutil.copyfile


def copy_dir(source, destination):
    # TODO: should be pure Python, but there isn't a stdlib function
    # that allows the destination to already exist
    local.run(["cp", "-rT", source, destination])


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if not (error.errno == errno.EEXIST and os.path.isdir(path)):
            raise


def delete_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def write_files(root_dir, file_descriptions):
    for file_description in file_descriptions:
        path = os.path.join(root_dir, file_description.path)
        if file_description.file_type == "dir":
            mkdir_p(path)
        elif file_description.file_type == "file":
            mkdir_p(os.path.dirname(path))
            write_file(path, file_description.contents)
            os.chmod(path, file_description.permissions)
        elif file_description.file_type == "symlink":
            os.symlink(file_description.contents, path)


def sh_script_description(path, contents):
    return FileDescription(path, "#!/bin/sh\n{0}".format(contents), 0o755, "file")


def directory_description(path):
    return FileDescription(path, None, permissions=None, file_type="dir")


def plain_file(path, contents):
    return FileDescription(path, contents, permissions=0o644, file_type="file")


def symlink(path, actual_path):
    return FileDescription(path, actual_path, permissions=None, file_type="symlink")


class FileDescription(object):
    def __init__(self, path, contents, permissions, file_type):
        self.path = path
        self.contents = contents
        self.permissions = permissions
        self.file_type = file_type
