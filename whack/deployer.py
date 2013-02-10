import os
import subprocess
import uuid


class PackageDeployer(object):
    def deploy(self, package_source, package_dir, install_dir):
        # TODO: should be pure Python, but there isn't a stdlib function
        # that allows the destination to already exist
        subprocess.check_call(["cp", "-rT", package_dir, install_dir])
        with open(os.path.join(install_dir, ".whack-root-id"), "w") as root_id_file:
            root_id_file.write(str(uuid.uuid4()))
