import re

import dodge

from .local import local_shell
from . import slugs


def generate_platform():
    generator = PlatformGenerator(local_shell)
    return generator.platform()


class PlatformGenerator(object):
    def __init__(self, shell):
        self._shell = shell
        
    def platform(self):
        os_name = self._uname("--kernel-name")
        architecture = self._uname("--machine")
        libc = self._run(["getconf", "GNU_LIBC_VERSION"])
        return Platform(os_name=os_name, architecture=architecture, libc=libc)
        
    def _uname(self, *args):
        return self._run(["uname"] + list(args))
        
    def _run(self, command):
        output =  self._shell.run(command).output
        return output.strip().lower().replace("_", "-").replace(" ", "-")


Platform = dodge.data_class("Platform", ["os_name", "architecture", "libc"])

Platform.dumps = lambda self: slugs.join(dodge.obj_to_flat_list(self))

Platform.load_list = staticmethod(lambda values: dodge.flat_list_to_obj(values, Platform))

def _platform_can_use(self, other):
    return (
        self.os_name == other.os_name and
        self.architecture == other.architecture and
        _libc_can_use(self.libc, other.libc)
    )
    
    
def _libc_can_use(first, second):
    first_version, second_version = map(_glibc_version, (first, second))
    if first_version is None or second_version is None:
        return first == second
    else:
        return first_version >= second_version
    

def _glibc_version(libc):
    result = re.match("^glibc-2.([0-9]+)(?:.([0-9]+))?$", libc)
    if result:
        if result.group(2) is None:
            patch_version = 0
        else:
            patch_version = int(result.group(2))
        return (int(result.group(1)), patch_version)
    else:
        return None


Platform.can_use = _platform_can_use
