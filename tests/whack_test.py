import os
import os.path
import contextlib
import tempfile
import subprocess
import shutil

from nose.tools import istest, assert_equal

from whack.builder import Builders

_HELLO_WORLD_BUILD = r"""#!/bin/sh
cat > hello << EOF
#!/bin/sh
echo Hello world!
EOF

chmod +x hello
"""

_HELLO_WORLD_INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""

@istest
def cli_application_is_installed_by_running_build_then_install_scripts():
    with _temporary_dir() as repo_dir, _temporary_dir() as install_dir:
        _create_test_builder(repo_dir, _HELLO_WORLD_BUILD, _HELLO_WORLD_INSTALL)
        
        subprocess.check_call(["whack", "install", "hello=1", install_dir, "--add-builder-repo", repo_dir])
        
        output = subprocess.check_output([os.path.join(install_dir, "hello")])
        assert_equal("Hello world!\n", output)

@istest
def application_is_installed_by_running_build_then_install_scripts():
    test_single_build(
        build=_HELLO_WORLD_BUILD,
        install=_HELLO_WORLD_INSTALL,
        expected_output="Hello world!\n"
    )

@istest
def version_is_passed_to_build_script():
    _TEST_BUILDER_BUILD = r"""#!/bin/sh
echo '#!/bin/sh' >> hello
echo echo ${VERSION} >> hello
chmod +x hello
"""

    _TEST_BUILDER_INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""
    test_single_build(
        build=_TEST_BUILDER_BUILD,
        install=_TEST_BUILDER_INSTALL,
        expected_output="1\n"
    )

def test_single_build(build, install, expected_output):
    for should_cache in [True, False]:
        with _temporary_dir() as repo_dir, _temporary_dir() as install_dir:
            _create_test_builder(repo_dir, build, install)
            
            builders = Builders(should_cache=should_cache, builder_repo_uris=[repo_dir])
            builders.build_and_install("hello=1", install_dir)
            
            output = subprocess.check_output([os.path.join(install_dir, "hello")])
            assert_equal(expected_output, output)

@contextlib.contextmanager
def _temporary_dir():
    try:
        build_dir = tempfile.mkdtemp()
        yield build_dir
    finally:
        shutil.rmtree(build_dir)

def _create_test_builder(repo_dir, build, install):
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
