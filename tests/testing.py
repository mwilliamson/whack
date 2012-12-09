import os
import os.path
import contextlib
import tempfile
import subprocess
import shutil

class HelloWorld(object):
    BUILD = r"""#!/bin/sh
cat > hello << EOF
#!/bin/sh
echo Hello world!
EOF

chmod +x hello
    """

    INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""

    EXPECTED_OUTPUT = "Hello world!\n"

@contextlib.contextmanager
def temporary_dir():
    try:
        build_dir = tempfile.mkdtemp()
        yield build_dir
    finally:
        shutil.rmtree(build_dir)

def create_test_builder(repo_dir, build, install):
    builder_dir = os.path.join(repo_dir, "hello")
    os.makedirs(builder_dir)
    _write_script(os.path.join(builder_dir, "build"), build)
    _write_script(os.path.join(builder_dir, "install"), install)
    
def _write_script(path, contents):
    _write_file(path, contents)
    _make_executable(path)

def _make_executable(path):
    subprocess.check_call(["chmod", "u+x", path])

def _write_file(path, contents):
    open(path, "w").write(contents)
