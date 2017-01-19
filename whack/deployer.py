import os
import stat

from .common import WHACK_ROOT
from .files import copy_dir
from . import local


class PackageDeployer(object):
    def deploy(self, package_dir, target_dir):
        copy_dir(os.path.join(package_dir, "dist"), target_dir)
        
