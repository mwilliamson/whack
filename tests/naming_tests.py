from nose.tools import istest, assert_equal

from whack.naming import PackageNamer


@istest
def package_with_unnamed_source_has_name_equal_to_install_identifier():
    package_source = PackageSource("/tmp/nginx-src", None, None)
    package_name = _name_package(package_source, {})
    assert_equal("install-id(/tmp/nginx-src, {})", package_name)


@istest
def params_are_passed_to_install_id_generator():
    package_source = PackageSource("/tmp/nginx-src", None, None)
    package_name = _name_package(package_source, {"version": "1.2"})
    assert_equal("install-id(/tmp/nginx-src, {'version': '1.2'})", package_name)
    

@istest
def package_with_named_source_has_name_equal_to_name_of_source_followed_by_install_identifier():
    package_source = PackageSource("/tmp/nginx-src", "nginx", None)
    package_name = _name_package(package_source, {})
    assert_equal("nginx-install-id(/tmp/nginx-src, {})", package_name)
    

@istest
def param_slug_is_included_if_present_in_description():
    package_source = PackageSource("/tmp/nginx-src", "nginx", "1.2")
    package_name = _name_package(package_source, {})
    assert_equal("nginx-1.2-install-id(/tmp/nginx-src, {})", package_name)


@istest
def format_string_is_expanded_in_param_slug():
    package_source = PackageSource("/tmp/nginx-src", "nginx", "{nginx_version}")
    package_name = _name_package(package_source, {"nginx_version": "1.2"})
    _assert_startswith(package_name, "nginx-1.2-install-id")


def _name_package(package_source, params):
    package_namer = PackageNamer(_generate_install_id)
    return package_namer.name_package(package_source, params)


def _generate_install_id(package_source, params):
    return "install-id({0}, {1})".format(package_source.path, params)


def _assert_startswith(string, prefix):
    if not string.startswith(prefix):
        raise AssertionError("{0} did not start with {1}".format(string, prefix))


class PackageSource(object):
    def __init__(self, path, name, param_slug):
        self.path = path
        self._name = name
        self._param_slug = param_slug
        
    def name(self):
        return self._name
        
    def description(self):
        return Description(self._param_slug)


class Description(object):
    def __init__(self, param_slug):
        self._param_slug = param_slug
        
    def param_slug(self):
        return self._param_slug
