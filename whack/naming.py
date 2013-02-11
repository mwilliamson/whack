import subprocess
import json

from .hashes import Hasher


def name_package(package_source, params):
    package_namer = PackageNamer(_generate_install_id_using_hash)
    return package_namer.name_package(package_source, params)


class PackageNamer(object):
    def __init__(self, generate_install_id):
        self._generate_install_id = generate_install_id
        
    def name_package(self, package_source, params):
        return self._generate_install_id(package_source.path, params)


def _generate_install_id_using_hash(package_src_dir, params):
    hasher = Hasher()
    hasher.update(_uname("--kernel-name"))
    hasher.update(_uname("--machine"))
    hasher.update_with_dir(package_src_dir)
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.hexdigest()


def _uname(arg):
    return subprocess.check_output(["uname", arg])
