from nose.tools import istest, assert_equal

from whack.packagerequests import PackageRequest
from whack.sources import DictBackedPackageDescription


@istest
def package_source_is_passed_to_install_id_generator():
    package_source = PackageSource("/tmp/nginx-src", {})
    package_name_parts = _name_parts_for_package(package_source, {})
    assert_equal("install-id(/tmp/nginx-src, {})", package_name_parts[-1])


@istest
def params_are_passed_to_install_id_generator():
    package_source = PackageSource("/tmp/nginx-src", {})
    package_name_parts = _name_parts_for_package(package_source, {"version": "1.2"})
    assert_equal("install-id(/tmp/nginx-src, {'version': '1.2'})", package_name_parts[-1])
    

@istest
def first_name_part_is_name_of_package_if_present():
    package_source = PackageSource("/tmp/nginx-src", {"name": "nginx"})
    package_name_parts = _name_parts_for_package(package_source, {})
    assert_equal("nginx", package_name_parts[0])
    

@istest
def param_slug_is_included_if_present_in_description():
    description = {"name": "nginx", "paramSlug": "1.2"}
    package_source = PackageSource("/tmp/nginx-src", description)
    package_name_parts = _name_parts_for_package(package_source, {})
    assert_equal("1.2", package_name_parts[1])


@istest
def format_string_is_expanded_in_param_slug():
    description = {"name": "nginx", "paramSlug": "{nginx_version}"}
    package_source = PackageSource("/tmp/nginx-src", description)
    package_name_parts = _name_parts_for_package(package_source, {"nginx_version": "1.2"})
    assert_equal("1.2", package_name_parts[1])


@istest
def default_params_are_used_in_param_slug_if_param_not_explicitly_set():
    description = {
        "name": "nginx",
        "paramSlug": "{nginx_version}",
        "defaultParams": {"nginx_version": "1.2"},
    }
    package_source = PackageSource("/tmp/nginx-src", description)
    package_name_parts = _name_parts_for_package(package_source, {})
    assert_equal("1.2", package_name_parts[1])


def _name_parts_for_package(package_source, params):
    request = PackageRequest(package_source, params, _generate_install_id)
    return request.name().split("_")


def _generate_install_id(package_source, params):
    return "install-id({0}, {1})".format(package_source.path, params)


class PackageSource(object):
    def __init__(self, path, description):
        self.path = path
        self._description = description
        
    def name(self):
        return self.description().name()
        
    def description(self):
        return DictBackedPackageDescription(self._description)
