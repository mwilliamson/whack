import os
import uuid

from .files import copy_dir


class PackageDeployer(object):
    def deploy(self, package_source, package_dir, install_dir):
        copy_dir(package_dir, install_dir)
        with open(os.path.join(install_dir, ".whack-root-id"), "w") as root_id_file:
            root_id_file.write(str(uuid.uuid4()))
