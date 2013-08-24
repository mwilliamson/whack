import collections

from .local import local_shell


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


Platform = collections.namedtuple("Platform", ["os_name", "architecture", "libc"])

    
