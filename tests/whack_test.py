import os
import os.path
import contextlib
import tempfile
import subprocess
import shutil

from nose.tools import istest, assert_equal

from whack.builder import Builders

@istest
def can_build_simple_application_with_install_dir_used_in_install_script():
    _TEST_BUILDER_BUILD = r"""#!/bin/sh
INSTALL_DIR=$1
cat > hello << EOF
#!/bin/sh
echo Hello there
EOF

chmod +x hello
"""

    _TEST_BUILDER_INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""
    test_single_build(
        build=_TEST_BUILDER_BUILD,
        install=_TEST_BUILDER_INSTALL,
        expected_output="Hello there\n"
    )

@istest
def can_build_simple_application_with_install_dir_used_in_build_script():
    test_single_build(
        build=_TEST_BUILDER_BUILD_USE_INSTALL_DIR_IN_BUILD,
        install=_TEST_BUILDER_INSTALL_USE_INSTALL_DIR_IN_BUILD,
        expected_output="Hello there\n"
    )

@istest
def changing_install_dir_results_in_rebuild_when_caching():
    with _temporary_dir() as repo_dir, _temporary_dir() as install_dir_1, _temporary_dir() as install_dir_2:
        _create_test_builder(repo_dir,
            _TEST_BUILDER_BUILD_USE_INSTALL_DIR_IN_BUILD,
            _TEST_BUILDER_INSTALL_USE_INSTALL_DIR_IN_BUILD
        )
        
        builders = Builders(should_cache=True, builder_repo_uris=[repo_dir])
        builders.build_and_install("hello=1", install_dir_1)
        builders.build_and_install("hello=1", install_dir_2)
        
        output = subprocess.check_output([os.path.join(install_dir_2, "hello")])
        assert_equal("Hello there\n", output)

@istest
def version_is_passed_to_build_script():
    _TEST_BUILDER_BUILD = r"""#!/bin/sh
INSTALL_DIR=$1
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

_TEST_BUILDER_BUILD_USE_INSTALL_DIR_IN_BUILD = r"""#!/bin/sh
INSTALL_DIR=$1
echo $INSTALL_DIR > install-dir
cat > hello << EOF
#!/bin/sh
echo Hello there
EOF

chmod +x hello
"""

_TEST_BUILDER_INSTALL_USE_INSTALL_DIR_IN_BUILD = r"""#!/bin/sh
INSTALL_DIR=`cat install-dir`
cp hello $INSTALL_DIR/hello
"""
