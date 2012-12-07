import argparse

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
        
        self._operations.install(
            package=args.package,
            install_dir=args.install_dir,
            builder_uris=args.add_builder_repo,
            should_cache=not args.no_cache,
            params=params
        )
        
_commands = {
    "install": InstallCommand,
}
