import os
import os.path
import subprocess
import contextlib

from nose.tools import istest, assert_equal

from whack.operations import Operations
from whack.sources import PackageSource
from whack.providers import create_package_provider
from whack.deployer import PackageDeployer
from catchy import NoCachingStrategy
import testing
from whack.tempdir import create_temporary_dir


test = istest


@test
def application_is_installed_by_running_build_with_install_dir_as_param():
    _BUILD = r"""#!/bin/sh
set -e
INSTALL_DIR=$1
mkdir -p $INSTALL_DIR/bin
cat > $INSTALL_DIR/bin/hello << EOF
#!/bin/sh
echo Hello there
EOF

chmod +x $INSTALL_DIR/bin/hello
"""
    with _temporary_install(_BUILD) as installation:
        output = subprocess.check_output(installation.install_path("bin/hello"))
        assert_equal("Hello there\n", output)


@test
def install_works_with_relative_path_for_install_dir():
    _BUILD = r"""#!/bin/sh
set -e
INSTALL_DIR=$1
mkdir -p $INSTALL_DIR/bin
cat > $INSTALL_DIR/bin/hello << EOF
#!/bin/sh
echo Hello there
EOF

chmod +x $INSTALL_DIR/bin/hello
"""

    with _temporary_package_source(_BUILD) as package_source_dir:
        with create_temporary_dir() as install_dir:
            with _change_dir(install_dir):
                _install(package_source_dir, ".")
    
            output = subprocess.check_output(os.path.join(install_dir, "bin/hello"))
            assert_equal("Hello there\n", output)
    

@test
def params_are_passed_as_uppercase_environment_variables_to_build_script():
    _BUILD = r"""#!/bin/sh
set -e
INSTALL_DIR=$1
mkdir -p $INSTALL_DIR/bin
cat > $INSTALL_DIR/bin/hello << EOF
#!/bin/sh
echo hello ${HELLO_VERSION}
EOF

chmod +x $INSTALL_DIR/bin/hello
"""
    with _temporary_install(_BUILD, params={"hello_version": 42}) as installation:
        output = subprocess.check_output(installation.install_path("bin/hello"))
    assert_equal("hello 42\n", output)


@test
def run_script_in_installation_mounts_whack_root_before_running_command():
    _BUILD = r"""#!/bin/sh
set -e
INSTALL_DIR=$1
mkdir -p $INSTALL_DIR/bin
echo 'Hello there' > $INSTALL_DIR/message
cat > $INSTALL_DIR/bin/hello << EOF
#!/bin/sh
cat $INSTALL_DIR/message
EOF

chmod +x $INSTALL_DIR/bin/hello
"""

    with _temporary_install(_BUILD) as installation:
        output = subprocess.check_output([
            installation.install_path("run"),
            installation.install_path("bin/hello"),
        ])
    assert_equal("Hello there\n", output)
    

@contextlib.contextmanager
def _temporary_install(build, params=None):
    with _temporary_package_source(build) as package_source_dir:
        with create_temporary_dir() as install_dir:
            _install(package_source_dir, install_dir, params=params)
            yield Installation(install_dir)


class SimplePackageSourceFetcher(object):
    @contextlib.contextmanager
    def fetch(self, package_name):
        yield PackageSource(package_name)


class Installation(object):
    def __init__(self, install_dir):
        self._install_dir = install_dir

    def install_path(self, path):
        return os.path.join(self._install_dir, path)


@contextlib.contextmanager
def _temporary_package_source(build):
    with create_temporary_dir() as package_source_dir:
        testing.write_package_source(package_source_dir, {"build": build})
        yield package_source_dir


def _install(*args, **kwargs):
    package_source_fetcher = SimplePackageSourceFetcher()
    package_provider = create_package_provider(cacher=NoCachingStrategy())
    deployer = PackageDeployer()
    operations = Operations(package_source_fetcher, package_provider, deployer)
    return operations.install(*args, **kwargs)


@contextlib.contextmanager
def _change_dir(new_dir):
    original_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(original_dir)
