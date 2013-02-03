from . import templates


class PackageDeployer(object):
    def __init__(self, package_provider):
        self._package_provider = package_provider
    
    def deploy(self, package_source, install_dir, params={}):
        with self._provide_package(package_source, params) as package_dir:
            template = templates.template(package_source.template_name())
            template.install(package_dir, install_dir)
            
    def _provide_package(self, package_source, params):
        return self._package_provider.provide_package(package_source, params)
