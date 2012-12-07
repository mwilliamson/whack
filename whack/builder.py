import os

from whack.installer import PackageInstaller, DirectoryCacher, NoCachingStrategy
from whack import downloads

class Builders(object):
    def __init__(self, should_cache, builder_repo_uris):
        self._should_cache = should_cache
        self._builder_repo_urls = builder_repo_uris

    def build_and_install(self, package_name, install_dir, params):
        scripts_dir = self._fetch_scripts(package_name)
        builder = PackageInstaller(scripts_dir, self._create_cacher())
        return builder.install(install_dir, params=params)

    def _fetch_scripts(self, package):
        for uri in self._builder_repo_urls:
            if self._is_local_uri(uri):
                repo_dir = uri
            else:
                repo_dir = downloads.fetch_source_control_uri(uri)
            # FIXME: race condition between this and when we acquire the lock
            package_dir = os.path.join(repo_dir, package)
            if os.path.exists(package_dir):
                return package_dir
                
        raise RuntimeError("No builders found for package: {0}".format(package))

    def _create_cacher(self):
        if self._should_cache:
            return DirectoryCacher(os.path.expanduser("~/.cache/whack/builds"))
        else:
            return NoCachingStrategy()
            
    def _is_local_uri(self, uri):
        return "://" not in uri



