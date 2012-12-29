import argparse
import os

import whack.config
import whack.args

env_default = whack.args.env_default(prefix="WHACK")


def main(argv, operations):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    for command_name, command_builder in _commands.iteritems():
        command = command_builder(operations)
        subparser = subparsers.add_parser(command_name)
        subparser.set_defaults(func=command.execute)
        command.create_parser(subparser)
    
    args = parser.parse_args(argv[1:])
    args.func(args)
    
class InstallCommand(object):
    def __init__(self, operations):
        self._operations = operations
    
    def create_parser(self, subparser):
        subparser.add_argument('package')
        subparser.add_argument('install_dir', metavar="install-dir")
        subparser.add_argument("--no-cache", action="store_true")
        subparser.add_argument("--http-cache-url", action=env_default)
        subparser.add_argument("--http-cache-key", action=env_default)
        subparser.add_argument("--add-builder-repo", action="append", default=[])
        subparser.add_argument("--add-parameter", "-p", action="append", default=[])
    
    def execute(self, args):
        params = {}
        for parameter_arg in args.add_parameter:
            if "=" in parameter_arg:
                key, value = parameter_arg.split("=", 1)
                params[key] = value
            else:
                params[parameter_arg] = ""
        
        caching = whack.config.caching_config(
            enabled=not args.no_cache,
            http_cache_url=args.http_cache_url,
            http_cache_key=args.http_cache_key
        )
        
        self._operations.install(
            package=args.package,
            install_dir=args.install_dir,
            builder_uris=args.add_builder_repo,
            caching=caching,
            params=params
        )

_commands = {
    "install": InstallCommand,
}
