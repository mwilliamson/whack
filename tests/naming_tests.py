from nose.tools import istest, assert_equal

from whack.naming import PackageNamer


@istest
def package_with_unnamed_source_has_name_equal_to_install_identifier():
    package_source = PackageSource("/tmp/nginx-src", None)
    package_name = _name_package(package_source, {})
    assert_equal("install-id(/tmp/nginx-src, {})", package_name)


def _name_package(package_source, params):
    package_namer = PackageNamer(_generate_install_id)
    return package_namer.name_package(package_source, {})


def _generate_install_id(source_dir_path, params):
    return "install-id({0}, {1})".format(source_dir_path, params)


class PackageSource(object):
    def __init__(self, path, name):
        self.path = path
        self._name = name
        
    def name(self):
        return self._name
