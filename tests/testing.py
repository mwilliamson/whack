import os
import os.path
import subprocess

from whack.files import write_file


class HelloWorld(object):
    BUILD = r"""#!/bin/sh
set -e
cd $1

cat > hello << EOF
#!/bin/sh
echo Hello world!
EOF

chmod +x hello
    """

    EXPECTED_OUTPUT = "Hello world!\n"

def write_package_source(package_dir, scripts):
    whack_dir = os.path.join(package_dir, "whack")
    os.makedirs(whack_dir)
    for name, contents in scripts.iteritems():
        _write_script(os.path.join(whack_dir, name), contents)

def _write_script(path, contents):
    write_file(path, contents)
    _make_executable(path)

def _make_executable(path):
    subprocess.check_call(["chmod", "u+x", path])
