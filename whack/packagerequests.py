class PackageRequest(object):
    def __init__(self, package_source, params):
        self._package_source = package_source
        self._params = params
        
    def params(self):
        default_params = self._package_source.description().default_params()
        params = default_params.copy()
        params.update(self._params)
        return params
