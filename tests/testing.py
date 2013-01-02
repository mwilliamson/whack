import os
import os.path
import contextlib
import tempfile
import subprocess
import shutil
import json

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

def create_test_builder(repo_dir, build, install):
    builder_dir = os.path.join(repo_dir, "hello")
    write_package(builder_dir, "relocatable", {"build": build, "install": install})

def write_package(package_dir, template_name, scripts):
    whack_dir = os.path.join(package_dir, "whack")
    os.makedirs(whack_dir)
    for name, contents in scripts.iteritems():
        _write_script(os.path.join(whack_dir, name), contents)
    whack_json = json.dumps({"template": template_name})
    open(os.path.join(whack_dir, "whack.json"), "w").write(whack_json)

def _write_script(path, contents):
    _write_file(path, contents)
    _make_executable(path)

def _make_executable(path):
    subprocess.check_call(["chmod", "u+x", path])

def _write_file(path, contents):
    open(path, "w").write(contents)

