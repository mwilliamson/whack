import os
import os.path
import contextlib
import tempfile
import subprocess
import shutil
import functools
import uuid

from nose.tools import istest, assert_equal

from whack.builder import Builders
from whack.installer import PackageInstaller, DirectoryCacher

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
    
    def create_local_package(self, **files):
        package_dir = self.create_temporary_dir()
        for name, contents in files.iteritems():
            _write_script(os.path.join(package_dir, name), contents)
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

    package_dir = test_runner.create_local_package(build=_BUILD, install=_INSTALL)
    install_dir = test_runner.install(package_dir, params={})
    
    output = subprocess.check_output(os.path.join(install_dir, "hello"))
    assert_equal("Hello there\n", output)
    
@test
def params_are_passed_as_environment_variables_to_build_script(test_runner):
    _BUILD = r"""#!/bin/sh
echo '#!/bin/sh' >> hello
echo echo hello ${HELLO_VERSION} >> hello
chmod +x hello
"""

    _INSTALL = r"""#!/bin/sh
INSTALL_DIR=$1
cp hello $INSTALL_DIR/hello
"""

    package_dir = test_runner.create_local_package(build=_BUILD, install=_INSTALL)
    install_dir = test_runner.install(package_dir, params={"HELLO_VERSION": 42})
    
    output = subprocess.check_output(os.path.join(install_dir, "hello"))
    assert_equal("hello 42\n", output)
    
@test
def result_of_build_command_is_reused_when_no_params_are_set(test_runner):
    build_log = test_runner.create_temporary_path()
    install_log = test_runner.create_temporary_path()
    
    _BUILD = r"""#!/bin/sh
echo building >> {0}
""".format(build_log)

    _INSTALL = r"""#!/bin/sh
echo installing >> {0}
""".format(install_log)

    package_dir = test_runner.create_local_package(build=_BUILD, install=_INSTALL)
    install_dir = test_runner.install(package_dir, params={})
    install_dir = test_runner.install(package_dir, params={})
    
    assert_equal("building\n", open(build_log).read())
    assert_equal("installing\ninstalling\n", open(install_log).read())

def _write_script(path, contents):
    _write_file(path, contents)
    _make_executable(path)

def _make_executable(path):
    subprocess.check_call(["chmod", "u+x", path])

def _write_file(path, contents):
    open(path, "w").write(contents)
