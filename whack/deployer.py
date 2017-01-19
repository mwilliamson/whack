import os
import stat

from .common import WHACK_ROOT
from .files import copy_dir
from . import local


class PackageDeployer(object):
    def deploy(self, package_dir, target_dir=None):
        if target_dir is None:
            install_dir = package_dir
        else:
            install_dir = target_dir
            copy_dir(package_dir, install_dir)
