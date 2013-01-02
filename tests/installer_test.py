import os
import os.path
import tempfile
import subprocess
import shutil
import functools
import uuid

from nose.tools import istest, assert_equal

from whack.installer import PackageInstaller
from catchy import DirectoryCacher
import testing

def test(func):
    @functools.wraps(func)
    def run_test():
        with TestRunner() as test_runner:
            func(test_runner)
    
    return istest(run_test)

class TestRunner(object):
    def __init__(self):
        self._test_dir = tempfile.mkdtemp()
        self._cacher = DirectoryCacher(os.path.join(self._test_dir, "cache"))
    
    def create_local_package(self, template_name, scripts):
        package_dir = self.create_temporary_dir()
        testing.write_package(package_dir, template_name, scripts)
        return package_dir
    
    def create_temporary_dir(self):
        temp_dir = self.create_temporary_path()
        os.mkdir(temp_dir)
        return temp_dir
        
    def create_temporary_path(self):
        return os.path.join(self._test_dir, str(uuid.uuid4()))

    def install(self, package_dir, params):
        install_dir = self.create_temporary_dir()
        
        installer = PackageInstaller(package_dir, cacher=self._cacher)
        installer.install(install_dir, params=params)
        return install_dir
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        shutil.rmtree(self._test_dir)

@test
def application_is_installed_by_running_build_then_install_scripts(test_runner):
    _BUILD = r"""#!/bin/sh
cat > hello << EOF
#!/bin/sh
echo Hello there
EOF

chmod +x hello
"""

    _INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""

    package_dir = test_runner.create_local_package(
        "relocatable",
        scripts={"build": _BUILD, "install": _INSTALL}
    )
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output(os.path.join(install_dir, "hello"))
    assert_equal("Hello there\n", output)
    
@test
def params_are_passed_as_uppercase_environment_variables_to_build_script(test_runner):
    _BUILD = r"""#!/bin/sh
echo '#!/bin/sh' >> hello
echo echo hello ${HELLO_VERSION} >> hello
chmod +x hello
"""

    _INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""

    package_dir = test_runner.create_local_package(
        "relocatable",
        scripts={"build": _BUILD, "install": _INSTALL}
    )
    install_dir = test_runner.install(package_dir, params={"hello_version": 42})
    
    output = subprocess.check_output(os.path.join(install_dir, "hello"))
    assert_equal("hello 42\n", output)
    
@test
def result_of_build_command_is_reused_when_no_params_are_set(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.install(package.package_dir, params={})
    test_runner.install(package.package_dir, params={})
    
    assert_equal("building\n", package.read_build_log())
    assert_equal("installing\ninstalling\n", package.read_install_log())
    
@test
def result_of_build_command_is_reused_when_params_are_the_same(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.install(package.package_dir, params={"VERSION": "2.4"})
    test_runner.install(package.package_dir, params={"VERSION": "2.4"})
    
    assert_equal("building\n", package.read_build_log())
    assert_equal("installing\ninstalling\n", package.read_install_log())
    
@test
def result_of_build_command_is_not_reused_when_params_are_not_the_same(test_runner):
    package = _create_logging_package(test_runner)
    test_runner.install(package.package_dir, params={"VERSION": "2.4"})
    test_runner.install(package.package_dir, params={"VERSION": "2.5"})
    
    assert_equal("building\nbuilding\n", package.read_build_log())
    assert_equal("installing\ninstalling\n", package.read_install_log())

@test
def non_relocatable_application_is_installed_by_running_build_with_install_dir_as_param(test_runner):
    _INSTALL = r"""#!/bin/sh
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
        "fixed-root",
        scripts={"install": _INSTALL}
    )
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output(os.path.join(install_dir, "bin/hello"))
    assert_equal("Hello there\n", output)
    
@test
def non_relocatable_application_can_be_run_using_run_script(test_runner):
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
        "fixed-root",
        scripts={"install": _INSTALL}
    )
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output([os.path.join(install_dir, "run"), "hello"])
    assert_equal("Hello there\n", output)
    
@test
def non_relocatable_application_under_bin_can_be_run_directly_if_binaries_are_placed_in_dot_bin(test_runner):
    _INSTALL = r"""#!/bin/sh
set -e
INSTALL_DIR=$1
mkdir -p $INSTALL_DIR/.bin
echo 'Hello there' > $INSTALL_DIR/message
cat > $INSTALL_DIR/.bin/hello << EOF
#!/bin/sh
cat $INSTALL_DIR/message
EOF

chmod +x $INSTALL_DIR/.bin/hello
"""

    package_dir = test_runner.create_local_package(
        "fixed-root",
        scripts={"install": _INSTALL}
    )
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output([os.path.join(install_dir, "bin/hello")])
    assert_equal("Hello there\n", output)
    
@test
def non_relocatable_application_under_sbin_can_be_run_directly_if_binaries_are_placed_in_dot_sbin(test_runner):
    _INSTALL = r"""#!/bin/sh
set -e
INSTALL_DIR=$1
mkdir -p $INSTALL_DIR/.sbin
echo 'Hello there' > $INSTALL_DIR/message
cat > $INSTALL_DIR/.sbin/hello << EOF
#!/bin/sh
cat $INSTALL_DIR/message
EOF

chmod +x $INSTALL_DIR/.sbin/hello
"""

    package_dir = test_runner.create_local_package(
        "fixed-root",
        scripts={"install": _INSTALL}
    )
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output([os.path.join(install_dir, "sbin/hello")])
    assert_equal("Hello there\n", output)
    
def _create_logging_package(test_runner):
    build_log = test_runner.create_temporary_path()
    install_log = test_runner.create_temporary_path()
    
    _BUILD = r"""#!/bin/sh
echo building >> {0}
""".format(build_log)

    _INSTALL = r"""#!/bin/sh
echo installing >> {0}
""".format(install_log)

    package_dir = test_runner.create_local_package(
        "relocatable",
        scripts={"build": _BUILD, "install": _INSTALL}
    )
    return LoggingPackage(package_dir, build_log, install_log)
    
class LoggingPackage(object):
    def __init__(self, package_dir, build_log, install_log):
        self.package_dir = package_dir
        self._build_log = build_log
        self._install_log = install_log
        
    def read_build_log(self):
        return open(self._build_log).read()
        
    def read_install_log(self):
        return open(self._install_log).read()

def _write_script(path, contents):
    _write_file(path, contents)
    _make_executable(path)

def _make_executable(path):
    subprocess.check_call(["chmod", "u+x", path])

def _write_file(path, contents):
    open(path, "w").write(contents)
