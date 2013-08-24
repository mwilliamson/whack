from nose.tools import istest, assert_equal

from whack.platform import PlatformGenerator


@istest
def platform_os_name_is_lower_case_result_of_uname_kernel_name():
    platform = _generate_platform()
    assert_equal(platform.os_name, "linux")


@istest
def platform_architecture_is_derived_from_uname_machine():
    platform = _generate_platform()
    assert_equal(platform.architecture, "x86-64")


@istest
def libc_version_is_derived_from_getconf_gnu_libc_version():
    platform = _generate_platform()
    assert_equal(platform.libc, "glibc-2.13")


def _generate_platform():
    generator = PlatformGenerator(shell=Shell())
    return generator.platform()


class Shell(object):
    def __init__(self):
        self._results = {
            ("uname", "--kernel-name"): ExecutionResult("Linux\n"),
            ("uname", "--machine"): ExecutionResult("x86_64\n"),
            ("getconf", "GNU_LIBC_VERSION"): ExecutionResult("glibc 2.13"),
        }
        
    def run(self, command):
        return self._results[tuple(command)]


class ExecutionResult(object):
    def __init__(self, output):
        self.output = output
