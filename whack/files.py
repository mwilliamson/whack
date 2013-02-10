import subprocess


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
