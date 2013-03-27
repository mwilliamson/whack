import json

from .hashes import Hasher
from . import local


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
    
    def name(self):
        params = self.params()
        source_name = self._package_source.name()
        param_slug = self._package_source.description().param_slug()
        param_part = self._generate_param_part(param_slug, params)
        install_id = self._generate_package_hash(self._package_source, params)
        
        name_parts = [source_name, param_part, install_id]
        
        return "-".join(part for part in name_parts if part)
        
    def _generate_param_part(self, slug, params):
        if slug is None:
            return None
        else:
            return slug.format(**params)


def _generate_install_id_using_hash(package_source, params):
    hasher = Hasher()
    hasher.update(_uname("--kernel-name"))
    hasher.update(_uname("--machine"))
    hasher.update(package_source.source_hash())
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.ascii_digest()


def _uname(arg):
    return local.run(["uname", arg]).output
