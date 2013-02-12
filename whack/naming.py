import subprocess
import json
import os

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
    for source_path in package_source.source_paths():
        absolute_source_path = os.path.join(package_source.path, source_path)
        hasher.update_with_dir(absolute_source_path)
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.ascii_digest()


def _uname(arg):
    return subprocess.check_output(["uname", arg])
