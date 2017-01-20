import os
import textwrap

from .files import copy_dir
from .tempdir import create_temporary_dir
from . import local


class PackageDeployer(object):
    def deploy(self, package_dir, target_dir):
        copy_dir(os.path.join(package_dir, "dist"), target_dir)
        deploy_path = os.path.join(package_dir, "src/whack/deploy")
        if os.path.exists(deploy_path):
            with open(os.path.join(package_dir, "dist-path"), "rb") as dist_path_file:
                original_dist_path = dist_path_file.read()
            
            with create_temporary_dir() as util_dir:
                rewrite_c_strings_path = os.path.join(util_dir, "whack-rewrite-c-strings")
                with open(rewrite_c_strings_path, "wb") as rewrite_c_strings_file:
                    rewrite_c_strings_file.write(textwrap.dedent(r"""
                        #!/usr/bin/env python
                        
                        import os
                        import sys
                        
                        dist_path = os.environ["WHACK_DIST_PATH"]
                        install_path = os.environ["WHACK_INSTALL_PATH"]
                        
                        assert len(dist_path) > len(install_path)
                        
                        target = sys.argv[1]
                        
                        # TODO: don't read the entire file in one go
                        with open(target, "rb") as fileobj:
                            contents = fileobj.read()
                        
                        # TODO: handle substrings
                        with open(target, "wb") as fileobj:
                            fileobj.write(contents.replace(dist_path + b"\0", install_path + b"\0" * (len(dist_path) - len(install_path) + 1)))
                    """).strip())
                os.chmod(rewrite_c_strings_path, 0o755)
            
                local.run([deploy_path], cwd=target_dir, update_env={
                    "PATH": "{}{}{}".format(util_dir, os.pathsep, os.environ["PATH"]),
                    "WHACK_DIST_PATH": original_dist_path,
                    "WHACK_INSTALL_PATH": target_dir,
                })
        
