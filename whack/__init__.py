import whack.builder

class WhackOperations(object):
    def install(self, package, install_dir, should_cache, builder_uris):
        builder = whack.builder.Builders(should_cache, builder_uris)
        builder.build_and_install(package, install_dir)
