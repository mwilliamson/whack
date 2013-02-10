def read_file(path):
    with open(path) as f:
        return f.read()
        

def write_file(path, contents):
    with open(path, "w") as f:
        f.write(contents)
