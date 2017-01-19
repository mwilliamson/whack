import os
import stat

from .common import WHACK_ROOT
from .files import copy_dir
from . import local


class PackageDeployer(object):
    def deploy(self, package_dir, target_dir):
        copy_dir(os.path.join(package_dir, "dist"), target_dir)
        deploy_path = os.path.join(package_dir, "src/whack/deploy")
        if os.path.exists(deploy_path):
            local.run([deploy_path], cwd=target_dir)
        
