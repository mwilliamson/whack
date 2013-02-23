import argparse

import whack.args

env_default = whack.args.env_default(prefix="WHACK")


def main(argv, create_operations):
    args = parse_args(argv)
    operations = create_operations(args.caching_enabled)
    args.func(operations, args)


def parse_args(argv):
    commands = [
        InstallCommand("install"),
        InstallCommand("build"),
        DeployCommand(),
        CreateSourceTarballCommand(),
    ]
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    for command in commands:
        subparser = subparsers.add_parser(command.name)
        _add_caching_args(subparser)
        subparser.set_defaults(func=command.execute)
        command.create_parser(subparser)

    return parser.parse_args(argv[1:])


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
    
    def execute(self, operations, args):
        if self.name == "install":
            operation = operations.install
        elif self.name == "build":
            operation = operations.build
        else:
            raise Exception("Unrecognised operation")
            
        operation(args.package, args.target_dir, params=args.params)


class DeployCommand(object):
    name = "deploy"
    
    def create_parser(self, subparser):
        subparser.add_argument('package_dir', metavar="package-dir")
        
        target_group = subparser.add_mutually_exclusive_group(required=True)
        target_group.add_argument("--in-place", action="store_true")
        target_group.add_argument("target_dir", metavar="target-dir", nargs="?")

    def execute(self, operations, args):
        operations.deploy(args.package_dir, args.target_dir)


class CreateSourceTarballCommand(object):
    name = "create-source-tarball"
    
    def create_parser(self, subparser):
        subparser.add_argument("package_source_dir", metavar="package-source-dir")
        subparser.add_argument("source_tarball_dir", metavar="source-tarball-dir")
        
    def execute(self, operations, args):
        source_tarball = operations.create_source_tarball(
            args.package_source_dir,
            args.source_tarball_dir
        )
        print source_tarball.full_name
        print source_tarball.path


def _add_caching_args(parser):
    parser.add_argument("--no-cache", action="store_false", dest="caching_enabled")
    
