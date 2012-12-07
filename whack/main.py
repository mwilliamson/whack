import argparse

import whack

class Main(object):
    def __init__(self, operations):
        self._operations = operations
    
    def main(self):
        commands = {
            "install": InstallCommand(self._operations),
        }

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        
        for command_name, command in commands.iteritems():
            subparser = subparsers.add_parser(command_name)
            subparser.set_defaults(func=command.execute)
            command.create_parser(subparser)
        
        args = parser.parse_args()
        args.func(args)
    
class InstallCommand(object):
    def __init__(self, operations):
        self._operations = operations
    
    def create_parser(self, subparser):
        subparser.add_argument('package')
        subparser.add_argument('install_dir', metavar="install-dir")
        subparser.add_argument("--no-cache", action="store_true")
        subparser.add_argument("--add-builder-repo", action="append", default=[])
    
    def execute(self, args):
        self._operations.install(
            package=args.package,
            install_dir=args.install_dir,
            should_cache=not args.no_cache,
            builder_uris=args.add_builder_repo
        )
