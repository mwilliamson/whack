import subprocess
import json

from .hashes import Hasher
from .packagerequests import PackageRequest


def name_package(package_source, params):
    package_namer = PackageNamer(_generate_install_id_using_hash)
    return package_namer.name_package(package_source, params)


class PackageNamer(object):
    def __init__(self, generate_install_id):
        self._generate_install_id = generate_install_id
        
    def name_package(self, package_source, params):
        request = PackageRequest(package_source, params)
        params = request.params()
        name = package_source.name()
        param_slug = package_source.description().param_slug()
        param_part = self._generate_param_part(param_slug, params)
        install_id = self._generate_install_id(package_source, params)
        
        name_parts = [name, param_part, install_id]
        
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
    return subprocess.check_output(["uname", arg])
