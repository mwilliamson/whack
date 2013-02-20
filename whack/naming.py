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
        install_id = self._generate_install_id(package_source, params)
        name = package_source.name()
        if name is None:
            return install_id
        else:
            return "{0}-{1}".format(name, install_id)


def _generate_install_id_using_hash(package_source, params):
    hasher = Hasher()
    hasher.update(_uname("--kernel-name"))
    hasher.update(_uname("--machine"))
    hasher.update(package_source.source_hash())
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.ascii_digest()


def _uname(arg):
    return subprocess.check_output(["uname", arg])
