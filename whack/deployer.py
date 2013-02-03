from . import templates


class PackageDeployer(object):
    def deploy(self, package_source, package_dir, install_dir):
        template = templates.template(package_source.template_name())
        template.install(package_dir, install_dir)
