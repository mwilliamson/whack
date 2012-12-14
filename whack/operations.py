import whack.builder

def install(package, install_dir, should_cache, builder_uris, params):
    builder = whack.builder.Builders(should_cache, builder_uris)
    builder.install(package, install_dir, params)
