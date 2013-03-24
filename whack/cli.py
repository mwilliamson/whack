import argparse
import sys

import whack.args
from whack.errors import WhackUserError

env_default = whack.args.env_default(prefix="WHACK")


def main(argv, create_operations):
    args = parse_args(argv)
    operations = create_operations(
        caching_enabled=args.caching_enabled,
        indices=args.indices,
        enable_build=args.enable_build,
    )
    try:
        exit(args.func(operations, args))
    except WhackUserError as error:
        sys.stderr.write("{0}: {1}\n".format(type(error).__name__, error.message))
        exit(1)


def parse_args(argv):
    commands = [
        InstallCommand("install"),
        InstallCommand("get-package"),
        DeployCommand(),
        CreateSourceTarballCommand(),
        GetPackageTarballCommand(),
        TestCommand(),
    ]
    
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    for command in commands:
        subparser = subparsers.add_parser(command.name)
        _add_common_args(subparser)
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
        subparser.add_argument('package_source', metavar="package-source")
        subparser.add_argument('target_dir', metavar="target-dir")
        _add_build_params_args(subparser)
    
    def execute(self, operations, args):
        if self.name == "install":
            operation = operations.install
        elif self.name == "get-package":
            operation = operations.get_package
        else:
            raise Exception("Unrecognised operation")
            
        operation(args.package_source, args.target_dir, params=args.params)


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
        subparser.add_argument('package_source', metavar="package-source")
        subparser.add_argument("source_tarball_dir", metavar="source-tarball-dir")
        
    def execute(self, operations, args):
        source_tarball = operations.create_source_tarball(
            args.package_source,
            args.source_tarball_dir
        )
        print source_tarball.full_name
        print source_tarball.path


class GetPackageTarballCommand(object):
    name = "get-package-tarball"
    
    def create_parser(self, subparser):
        subparser.add_argument("package")
        subparser.add_argument("package_tarball_dir", metavar="package-tarball-dir")
        _add_build_params_args(subparser)
        
    def execute(self, operations, args):
        package_tarball = operations.get_package_tarball(
            args.package,
            args.package_tarball_dir,
            params=args.params,
        )
        print package_tarball.path


class TestCommand(object):
    name = "test"
    
    def create_parser(self, subparser):
        subparser.add_argument('package_source', metavar="package-source")
        _add_build_params_args(subparser)
        
    def execute(self, operations, args):
        test_result = operations.test(args.package_source, params=args.params)
        if test_result.passed:
            return 0
        else:
            return 1


def _add_common_args(parser):
    _add_caching_args(parser)
    _add_index_args(parser)
    _add_build_args(parser)


def _add_caching_args(parser):
    parser.add_argument("--disable-cache", action="store_false", dest="caching_enabled")


def _add_index_args(parser):
    parser.add_argument(
        "--add-index",
        action="append",
        default=[],
        dest="indices",
        metavar="INDEX",
    )


def _add_build_args(parser):
    parser.add_argument("--disable-build", action="store_false", dest="enable_build")


def _add_build_params_args(parser):
    parser.add_argument(
        "--add-parameter", "-p",
        action=KeyValueAction,
        dest="params",
        metavar="KEY=VALUE",
    )
