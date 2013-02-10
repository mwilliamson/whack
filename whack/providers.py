import os
import subprocess
import shutil
import json
import contextlib
import stat

from . import downloads
from .hashes import Hasher
from .tempdir import create_temporary_dir


_WHACK_ROOT = "/usr/local/whack"


class BuildingPackageProvider(object):
    @contextlib.contextmanager
    def provide_package(self, package_src, params):
        with create_temporary_dir() as temp_dir:
            build_dir = os.path.join(temp_dir, "build")
            package_dir = os.path.join(temp_dir, "package")
            
            self._build(package_src, build_dir, package_dir, params)
                
            yield package_dir
    
    def _build(self, package_src, build_dir, package_dir, params):
        ignore = shutil.ignore_patterns(".svn", ".hg", ".hgignore", ".git", ".gitignore")
        shutil.copytree(package_src.path, build_dir, ignore=ignore)
        build_env = params_to_build_env(params)
        self._fetch_downloads(build_dir, build_env)
        
        def run(command):
            subprocess.check_call(
                command,
                cwd=build_dir,
                env=build_env
            )
            
        install_script = os.path.join(build_dir, "whack/build")
        os.mkdir(package_dir)
        run([
            "whack-run-with-whack-root",
            package_dir,
            install_script,
            _WHACK_ROOT
        ])
                
        with open(os.path.join(package_dir, "run"), "w") as run_file:
            run_file.write('#!/usr/bin/env sh\nexec whack-run-with-whack-root "$(dirname $0)" "$@"')
        subprocess.check_call(["chmod", "+x", os.path.join(package_dir, "run")])
        
        self._create_bin_dir(package_dir, "bin")
        self._create_bin_dir(package_dir, "sbin")

    def _fetch_downloads(self, build_dir, build_env):
        downloads_file_path = os.path.join(build_dir, "whack/downloads")
        downloads_file = self._read_downloads_file(downloads_file_path, build_env)
        for download_line in downloads_file:
            downloads.download(download_line.url, os.path.join(build_dir, download_line.filename))

    def _read_downloads_file(self, path, build_env):
        if os.path.exists(path):
            first_line = open(path).readline()
            if first_line.startswith("#!"):
                downloads_string = subprocess.check_output(
                    [path],
                    env=build_env
                )
            else:
                downloads_string = open(path).read()
                
            return downloads.read_downloads_string(downloads_string)
        else:
            return []
            
    
    def _create_bin_dir(self, install_dir, bin_dir_name):
        def install_path(path):
            return os.path.join(install_dir, path)
        
        dot_bin_dir = install_path(".{0}".format(bin_dir_name))
        bin_dir = install_path(bin_dir_name)
        if os.path.exists(dot_bin_dir):
            if not os.path.exists(bin_dir):
                os.mkdir(bin_dir)
            for bin_filename in self._list_missing_executable_files(install_dir, dot_bin_dir, bin_dir):
                bin_file_path = os.path.join(bin_dir, bin_filename)
                with open(bin_file_path, "w") as bin_file:
                    bin_file.write(
                        '#!/usr/bin/env sh\n\n' +
                        'TARGET="$(dirname $0)/../.{0}/{1}"\n'.format(bin_dir_name, bin_filename) +
                        'ACTIVE_ROOT_ID_FILE=\'{0}\'\n'.format(_WHACK_ROOT) +
                        'MY_ROOT_ID=`cat $(dirname $0)/../.whack-root-id`\n' +
                        'ACTIVE_ROOT_ID=`cat "$ACTIVE_ROOT_ID_FILE" 2>/dev/null`\n' +
                        'if [ -f "$ACTIVE_ROOT_ID_FILE" ] && [ "$MY_ROOT_ID" = "$ACTIVE_ROOT_ID" ]; then\n' +
                        'exec "$TARGET" "$@"\n' +
                        'else\n' +
                        'exec "$(dirname $0)/../run" "$TARGET" "$@"\n' +
                        'fi\n'
                    )
                os.chmod(bin_file_path, 0755)
    
    def _list_missing_executable_files(self, root_dir, dot_bin_dir, bin_dir):
        def is_missing(filename):
            return not os.path.exists(os.path.join(bin_dir, filename))
        return filter(is_missing, self._list_executable_files(root_dir, dot_bin_dir))
    
    def _list_executable_files(self, root_dir, dir_path):
        def is_executable_file(filename):
            path = os.path.join(dir_path, filename)
            while os.path.islink(path):
                link_target = os.readlink(path)
                if os.path.exists(link_target):
                    # Valid symlink
                    path = link_target
                elif link_target.startswith("{0}/".format(_WHACK_ROOT)):
                    # Valid symlink, but what root isn't mounted
                    path = os.path.join(root_dir, link_target[len(_WHACK_ROOT) + 1:])
                else:
                    # Broken symlink
                    return False
            
            if os.path.exists(path):
                is_executable = stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
                return not os.path.isdir(path) and is_executable
            else:
                return False
                
        return filter(is_executable_file, os.listdir(dir_path))


class CachingPackageProvider(object):
    def __init__(self, cacher):
        self._cacher = cacher
        self._underlying_provider = BuildingPackageProvider()
    
    @contextlib.contextmanager
    def provide_package(self, package_source, params):
        install_id = _generate_install_id(package_source.path, params)
        
        with create_temporary_dir() as temp_dir:
            cached_package_dir = os.path.join(temp_dir, "package")
            
            result = self._cacher.fetch(install_id, cached_package_dir)
            
            if result.cache_hit:
                yield cached_package_dir
            else:
                with self._underlying_provider.provide_package(package_source, params) as package_dir:
                    self._cacher.put(install_id, package_dir)
                    yield package_dir


def params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env
    

def _generate_install_id(package_src_dir, params):
    hasher = Hasher()
    hasher.update(_uname("--kernel-name"))
    hasher.update(_uname("--machine"))
    hasher.update_with_dir(package_src_dir)
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.hexdigest()


def _uname(arg):
    return subprocess.check_output(["uname", arg])
