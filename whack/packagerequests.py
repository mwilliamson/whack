import json

import dodge

from .hashes import Hasher
from . import local
from .platform import generate_platform, Platform


class PackageRequest(object):
    def __init__(self, package_source, params=None, generate_package_hash=None):
        if params is None:
            params = {}
        if generate_package_hash is None:
            generate_package_hash = _generate_install_id_using_hash
            
        self._package_source = package_source
        self._params = params
        self._generate_package_hash = generate_package_hash
    
    @property
    def source_uri(self):
        return self._package_source.uri
    
    def write_source_to(self, *args, **kwargs):
        return self._package_source.write_to(*args, **kwargs)
    
    def params(self):
        default_params = self._package_source.description().default_params()
        params = default_params.copy()
        params.update(self._params)
        return params
    
    def _name_parts(self):
        params = self.params()
        source_name = self._package_source.name()
        
        param_slug = self._package_source.description().param_slug()
        param_part = self._generate_param_part(param_slug, params)
        
        platform = generate_platform()
        
        install_id = self._generate_package_hash(self._package_source, params)
        
        return filter(
            lambda part: part,
            [source_name, param_part] + dodge.obj_to_dict(platform).values() + [install_id],
        )
    
    def name(self):
        return "_".join(part for part in self._name_parts())
        
    def describe(self):
        return PackageDescription(
            name=self.name(),
            source_name=self._package_source.name(),
            source_hash=self._package_source.source_hash(),
            params=self.params(),
            platform=generate_platform(),
        )
        
    def _generate_param_part(self, slug, params):
        if slug is None:
            return None
        else:
            return slug.format(**params)


def _generate_install_id_using_hash(package_source, params):
    hasher = Hasher()
    
    platform = generate_platform()
    for value in dodge.obj_to_dict(platform).values():
        hasher.update(value)
        
    hasher.update(package_source.source_hash())
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.ascii_digest()


def _uname(arg):
    return local.run(["uname", arg]).output


PackageDescription = dodge.data_class("PackageDescription", [
    "name",
    "source_name",
    "source_hash",
    "params",
    dodge.field("platform", type=Platform),
])
