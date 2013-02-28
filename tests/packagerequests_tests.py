from nose.tools import istest, assert_equal

from whack.packagerequests import PackageRequest
from whack.sources import DictBackedPackageDescription


@istest
def package_with_unnamed_source_has_name_equal_to_install_identifier():
    package_source = PackageSource("/tmp/nginx-src", {})
    package_name = _name_package(package_source, {})
    assert_equal("install-id(/tmp/nginx-src, {})", package_name)


@istest
def params_are_passed_to_install_id_generator():
    package_source = PackageSource("/tmp/nginx-src", {})
    package_name = _name_package(package_source, {"version": "1.2"})
    assert_equal("install-id(/tmp/nginx-src, {'version': '1.2'})", package_name)
    

@istest
def package_with_named_source_has_name_equal_to_name_of_source_followed_by_install_identifier():
    package_source = PackageSource("/tmp/nginx-src", {"name": "nginx"})
    package_name = _name_package(package_source, {})
    assert_equal("nginx-install-id(/tmp/nginx-src, {})", package_name)
    

@istest
def param_slug_is_included_if_present_in_description():
    description = {"name": "nginx", "paramSlug": "1.2"}
    package_source = PackageSource("/tmp/nginx-src", description)
    package_name = _name_package(package_source, {})
    assert_equal("nginx-1.2-install-id(/tmp/nginx-src, {})", package_name)


@istest
def format_string_is_expanded_in_param_slug():
    description = {"name": "nginx", "paramSlug": "{nginx_version}"}
    package_source = PackageSource("/tmp/nginx-src", description)
    package_name = _name_package(package_source, {"nginx_version": "1.2"})
    _assert_startswith(package_name, "nginx-1.2-install-id")


@istest
def default_params_are_used_in_param_slug_if_param_not_explicitly_set():
    description = {
        "name": "nginx",
        "paramSlug": "{nginx_version}",
        "defaultParams": {"nginx_version": "1.2"},
    }
    package_source = PackageSource("/tmp/nginx-src", description)
    package_name = _name_package(package_source, {})
    _assert_startswith(package_name, "nginx-1.2-install-id")


def _name_package(package_source, params):
    request = PackageRequest(package_source, params, _generate_install_id)
    return request.name()


def _generate_install_id(package_source, params):
    return "install-id({0}, {1})".format(package_source.path, params)


def _assert_startswith(string, prefix):
    if not string.startswith(prefix):
        raise AssertionError("{0} did not start with {1}".format(string, prefix))


class PackageSource(object):
    def __init__(self, path, description):
        self.path = path
        self._description = description
        
    def name(self):
        return self.description().name()
        
    def description(self):
        return DictBackedPackageDescription(self._description)


class Description(object):
    def __init__(self, param_slug):
        self._param_slug = param_slug
        
    def param_slug(self):
        return self._param_slug
