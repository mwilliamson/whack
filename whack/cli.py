import argparse

import whack.config
import whack.args

env_default = whack.args.env_default(prefix="WHACK")


def main(argv, operations):
    args = parse_args(argv)
    args.func(operations, args)


def parse_args(argv):
    commands = [
        InstallCommand("install"),
        InstallCommand("build"),
    ]
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    for command in commands:
        subparser = subparsers.add_parser(command.name)
        subparser.set_defaults(func=command.execute)
        command.create_parser(subparser)

    return parser.parse_args(argv[1:])
    
class InstallCommand(object):
    def __init__(self, name):
        self.name = name
    
    def create_parser(self, subparser):
        subparser.add_argument('package')
        subparser.add_argument('target_dir', metavar="target-dir")
        subparser.add_argument("--no-cache", action="store_true")
        subparser.add_argument("--http-cache-url", action=env_default)
        subparser.add_argument("--http-cache-key", action=env_default)
        subparser.add_argument("--add-parameter", "-p", action="append", default=[])
    
    def execute(self, operations, args):
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
        
        if self.name == "install":
            operation = operations.install
        elif self.name == "build":
            operation = operations.build
        else:
            raise Exception("Unrecognised operation")
            
        operation(
            package=args.package,
            install_dir=args.target_dir,
            caching=caching,
            params=params
        )
