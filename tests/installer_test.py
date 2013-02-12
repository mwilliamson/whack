import os
import os.path
import tempfile
import subprocess
import shutil
import functools
import uuid
import contextlib

from nose.tools import istest, assert_equal

from whack.installer import Installer
from whack.sources import PackageSource
from whack.providers import CachingPackageProvider
from whack.deployer import PackageDeployer
from catchy import DirectoryCacher
import testing


def test(func):
    @functools.wraps(func)
    def run_test():
        with TestRunner() as test_runner:
            func(test_runner)
    
    return istest(run_test)


class InMemoryPackageSourceFetcher(object):
    def __init__(self, package_sources):
        self._package_sources = package_sources

    @contextlib.contextmanager
    def fetch(self, package_name):
        yield PackageSource(self._package_sources[package_name])


class TestRunner(object):
    def __init__(self):
        self._test_dir = tempfile.mkdtemp()
        self._cacher = DirectoryCacher(os.path.join(self._test_dir, "cache"))
    
    def create_local_package(self, scripts):
        package_dir = self.create_temporary_dir()
        testing.write_package_source(package_dir, scripts)
        return package_dir
    
    def create_temporary_dir(self):
        temp_dir = self.create_temporary_path()
        os.mkdir(temp_dir)
        return temp_dir
        
    def create_temporary_path(self):
        return os.path.join(self._test_dir, str(uuid.uuid4()))

    def install(self, package_dir, params):
        install_dir = self.create_temporary_dir()
        return self.install_to_dir(package_dir, params, install_dir)
        
    def install_to_dir(self, package_dir, params, install_dir):
        package_name = "test-package"
        
        package_source_fetcher = InMemoryPackageSourceFetcher({
            package_name: package_dir
        })
        package_provider = CachingPackageProvider(self._cacher)
        deployer = PackageDeployer()
        installer = Installer(package_source_fetcher, package_provider, deployer)
        
        installer.install(package_name, install_dir, params=params)
        return install_dir
        
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        shutil.rmtree(self._test_dir)


@test
def application_is_installed_by_running_build_with_install_dir_as_param(test_runner):
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

    package_dir = test_runner.create_local_package(
        scripts={"build": _BUILD}
    )
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output(os.path.join(install_dir, "bin/hello"))
    assert_equal("Hello there\n", output)


@test
def install_works_with_relative_path_for_install_dir(test_runner):
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

    package_dir = test_runner.create_local_package(
        scripts={"build": _BUILD}
    )
    install_dir = test_runner.create_temporary_dir()
    original_dir = os.getcwd()
    try:
        os.chdir(install_dir)
        test_runner.install_to_dir(package_dir, params={}, install_dir=".")
    finally:
        os.chdir(original_dir)
        
    
    output = subprocess.check_output(os.path.join(install_dir, "bin/hello"))
    assert_equal("Hello there\n", output)
    

@test
def params_are_passed_as_uppercase_environment_variables_to_build_script(test_runner):
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

    package_dir = test_runner.create_local_package(
        scripts={"build": _BUILD}
    )
    install_dir = test_runner.install(package_dir, params={"hello_version": 42})
    
    output = subprocess.check_output(os.path.join(install_dir, "bin/hello"))
    assert_equal("hello 42\n", output)


@test
def run_script_in_installation_mounts_whack_root_before_running_command(test_runner):
    _INSTALL = r"""#!/bin/sh
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

    package_dir = test_runner.create_local_package(
        scripts={"build": _INSTALL}
    )
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output([os.path.join(install_dir, "run"), "hello"])
    assert_equal("Hello there\n", output)
    
    
@test
def result_of_build_command_is_reused_when_no_params_are_set(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.install(package.package_dir, params={})
    test_runner.install(package.package_dir, params={})
    
    assert_equal("building\n", package.read_build_log())
    
    
@test
def result_of_build_command_is_reused_when_params_are_the_same(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.install(package.package_dir, params={"VERSION": "2.4"})
    test_runner.install(package.package_dir, params={"VERSION": "2.4"})
    
    assert_equal("building\n", package.read_build_log())
    
    
@test
def result_of_build_command_is_not_reused_when_params_are_not_the_same(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.install(package.package_dir, params={"VERSION": "2.4"})
    test_runner.install(package.package_dir, params={"VERSION": "2.5"})
    
    assert_equal("building\nbuilding\n", package.read_build_log())
    
    
def _create_logging_package(test_runner):
    build_log = test_runner.create_temporary_path()
    
    _BUILD = r"""#!/bin/sh
echo building >> {0}
""".format(build_log)

    package_dir = test_runner.create_local_package(
        scripts={"build": _BUILD}
    )
    return LoggingPackage(package_dir, build_log)
    
    
class LoggingPackage(object):
    def __init__(self, package_dir, build_log):
        self.package_dir = package_dir
        self._build_log = build_log
        
    def read_build_log(self):
        return open(self._build_log).read()


def _write_script(path, contents):
    _write_file(path, contents)
    _make_executable(path)


def _make_executable(path):
    subprocess.check_call(["chmod", "u+x", path])


def _write_file(path, contents):
    open(path, "w").write(contents)
