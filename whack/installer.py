import os
import subprocess
import shutil
import json
import uuid
import stat

from whack import downloads
from whack.hashes import Hasher
from whack.tempdir import create_temporary_dir

__all__ = ["PackageInstaller"]

_WHACK_ROOT = "/usr/local/whack"


class RelocatableTemplate(object):
    def install_to_cache(self, run, build_dir, working_dir):
        build_script = os.path.join(working_dir, "whack/build")
        run([build_script])
        
    def install_from_cache(self, build_dir, working_dir, install_dir):
        subprocess.check_call(
            [os.path.join(working_dir, "whack/install"), install_dir],
            cwd=working_dir
        )
     
        
class FixedRootTemplate(object):
    def install_to_cache(self, run, build_dir, working_dir):
        install_script = os.path.join(working_dir, "whack/install")
        install_dir = self._cached_install_dir(build_dir)
        os.mkdir(install_dir)
        run([
            "whack-run-with-whack-root",
            install_dir,
            install_script,
            _WHACK_ROOT
        ])
                
        with open(os.path.join(install_dir, "run"), "w") as run_file:
            run_file.write('#!/usr/bin/env sh\nexec whack-run-with-whack-root "$(dirname $0)" "$@"')
        subprocess.check_call(["chmod", "+x", os.path.join(install_dir, "run")])
        
        self._create_bin_dir(install_dir, "bin")
        self._create_bin_dir(install_dir, "sbin")
    
    def _create_bin_dir(self, install_dir, bin_dir_name):
        def install_path(path):
            return os.path.join(install_dir, path)
        
        dot_bin_dir = install_path(".{0}".format(bin_dir_name))
        bin_dir = install_path(bin_dir_name)
        if os.path.exists(dot_bin_dir) and not os.path.exists(bin_dir):
            os.mkdir(bin_dir)
            for bin_filename in self._list_executable_files(dot_bin_dir):
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
        
    def _list_executable_files(self, dir_path):
        def is_executable_file(filename):
            path = os.path.join(dir_path, filename)
            is_executable = stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
            return not os.path.isdir(path) and is_executable
        return filter(is_executable_file, os.listdir(dir_path))
    
    def install_from_cache(self, build_dir, working_dir, install_dir):
        cached_install_dir = self._cached_install_dir(build_dir)
        # TODO: should be pure Python, but there isn't a stdlib function
        # that allows the destination to already exist
        subprocess.check_call(["cp", "-rT", cached_install_dir, install_dir])
        with open(os.path.join(install_dir, ".whack-root-id"), "w") as root_id_file:
            root_id_file.write(str(uuid.uuid4()))
        
    def _cached_install_dir(self, build_dir):
        return os.path.join(build_dir, "install")


_templates = {
    "fixed-root": FixedRootTemplate(),
    "relocatable": RelocatableTemplate()
}

_default_template_name = "relocatable"

class PackageInstaller(object):
    def __init__(self, package_dir, cacher):
        self._package_dir = package_dir
        self._cacher = cacher
    
    def install(self, install_dir, params={}):
        install_id = _generate_install_id(self._package_dir, params)
        
        with create_temporary_dir() as temp_dir:
            build_dir = os.path.join(temp_dir, "build")
            working_dir = os.path.join(build_dir, "workspace")
            
            result = self._cacher.fetch(install_id, working_dir)
            if not result.cache_hit:
                self._build(build_dir, working_dir, params)
                self._cacher.put(install_id, working_dir)
            
            self._template().install_from_cache(build_dir, working_dir, install_dir)

    def _build(self, build_dir, working_dir, params):
        ignore = shutil.ignore_patterns(".svn", ".hg", ".hgignore", ".git", ".gitignore")
        shutil.copytree(self._package_dir, working_dir, ignore=ignore)
        build_env = params_to_build_env(params)
        self._fetch_downloads(working_dir, build_env)
        
        def run(command):
            subprocess.check_call(
                command,
                cwd=working_dir,
                env=build_env
            )
            
        self._template().install_to_cache(run, build_dir, working_dir)

    def _template(self):
        return _templates[self._template_name()]

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
            
    def _template_name(self):
        return _read_package_description(self._package_dir).template_name
        

def params_to_build_env(params):
    build_env = os.environ.copy()
    for name, value in (params or {}).iteritems():
        build_env[name.upper()] = str(value)
    return build_env


def _generate_install_id(package_dir, params):
    hasher = Hasher()
    hasher.update(_uname("--kernel-name"))
    hasher.update(_uname("--machine"))
    hasher.update_with_dir(package_dir)
    hasher.update(json.dumps(params, sort_keys=True))
    return hasher.hexdigest()

def _uname(arg):
    return subprocess.check_output(["uname", arg])


def _read_package_description(package_dir):
    whack_json_path = os.path.join(package_dir, "whack/whack.json")
    if os.path.exists(whack_json_path):
        with open(whack_json_path, "r") as whack_json_file:
            whack_json = json.load(whack_json_file)
        return DictBackedPackageDescription(whack_json)
    else:
        return DefaultPackageDescription()
        
        
class DefaultPackageDescription(object):
    template_name = _default_template_name


class DictBackedPackageDescription(object):
    def __init__(self, values):
        self._values = values
    
    @property
    def template_name(self):
        return self._values.get("template", _default_template_name)
