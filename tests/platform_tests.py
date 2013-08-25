from nose.tools import istest, assert_equal

from whack.platform import PlatformGenerator, Platform


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


@istest
def can_use_other_glibc_if_minor_version_is_the_same():
    assert _platform_with_libc("glibc-2.13").can_use(_platform_with_libc("glibc-2.12"))


@istest
def can_use_other_glibc_if_minor_version_is_lower():
    assert _platform_with_libc("glibc-2.13").can_use(_platform_with_libc("glibc-2.12"))


@istest
def cannot_use_other_glibc_if_minor_version_is_higher():
    assert not _platform_with_libc("glibc-2.13").can_use(_platform_with_libc("glibc-2.14"))


@istest
def minor_version_comparison_is_numerical_rather_than_lexical():
    assert not _platform_with_libc("glibc-2.13").can_use(_platform_with_libc("glibc-2.101"))


@istest
def version_must_match_exactly_if_major_version_is_not_2():
    assert not _platform_with_libc("glibc-1.13").can_use(_platform_with_libc("glibc-1.12"))


@istest
def can_use_other_glibc_if_patch_version_is_the_same():
    assert _platform_with_libc("glibc-2.3.6").can_use(_platform_with_libc("glibc-2.3.6"))


@istest
def can_use_other_glibc_if_patch_version_is_lower():
    assert _platform_with_libc("glibc-2.3.5").can_use(_platform_with_libc("glibc-2.3.4"))


@istest
def cannot_use_other_glibc_if_patch_version_is_higher():
    assert not _platform_with_libc("glibc-2.3.5").can_use(_platform_with_libc("glibc-2.3.6"))


@istest
def patch_version_comparison_is_numerical_rather_than_lexical():
    assert not _platform_with_libc("glibc-2.3.5").can_use(_platform_with_libc("glibc-2.3.40"))


@istest
def minor_version_takes_precendence_over_patch_version():
    assert _platform_with_libc("glibc-2.3.5").can_use(_platform_with_libc("glibc-2.2.6"))
    assert not _platform_with_libc("glibc-2.2.6").can_use(_platform_with_libc("glibc-2.3.5"))


def _platform_with_libc(libc):
    return Platform(
        os_name="linux",
        architecture="x86-64",
        libc=libc,
    )


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
