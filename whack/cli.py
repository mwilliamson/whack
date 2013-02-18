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
        DeployCommand(),
    ]
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    for command in commands:
        subparser = subparsers.add_parser(command.name)
        subparser.set_defaults(func=command.execute)
        command.create_parser(subparser)

    args = parser.parse_args(argv[1:])

    args.caching = whack.config.caching_config(
            enabled=not args.no_cache,
            http_cache_url=args.http_cache_url,
            http_cache_key=args.http_cache_key
        )

    return args


class KeyValueAction(argparse.Action):
    def __init__(self, default=None, **kwargs):
        if default is None:
            default = {}
            
        super(type(self), self).__init__(default=default, **kwargs)
    
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is None:
            setattr(namespace, self.dest, {})
        
        pairs = getattr(namespace, self.dest)
        if "=" in values:
            key, value = values.split("=", 1)
            pairs[key] = value
        else:
            pairs[values] = ""
        
        setattr(namespace, self.dest, pairs)


class InstallCommand(object):
    def __init__(self, name):
        self.name = name
    
    def create_parser(self, subparser):
        subparser.add_argument('package')
        subparser.add_argument('target_dir', metavar="target-dir")
        subparser.add_argument(
            "--add-parameter", "-p",
            action=KeyValueAction,
            dest="params",
        )
        _add_caching_args(subparser)
    
    def execute(self, operations, args):
        if self.name == "install":
            operation = operations.install
        elif self.name == "build":
            operation = operations.build
        else:
            raise Exception("Unrecognised operation")
            
        operation(
            package=args.package,
            install_dir=args.target_dir,
            caching=args.caching,
            params=args.params
        )


class DeployCommand(object):
    name = "deploy"
    
    def create_parser(self, subparser):
        subparser.add_argument('package_dir', metavar="package-dir")
        _add_caching_args(subparser)

    def execute(self, operations, args):
        operations.deploy(args.package_dir, args.caching)


def _add_caching_args(parser):
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--http-cache-url", action=env_default)
    parser.add_argument("--http-cache-key", action=env_default)
    
