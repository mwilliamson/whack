import argparse
import os

import whack.config


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
        subparser.add_argument("--http-cache-url", action=EnvDefault)
        subparser.add_argument("--add-builder-repo", action="append", default=[])
        subparser.add_argument("--add-parameter", "-p", action="append", default=[])
    
    def _add_argument_with_environment_default(self, subparser, name, env_var):
        subparser.add_argument(name, default=os.environ.get(env_var))
    
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
            http_cache_url=args.http_cache_url
        )
        
        self._operations.install(
            package=args.package,
            install_dir=args.install_dir,
            builder_uris=args.add_builder_repo,
            caching=caching,
            params=params
        )

class EnvDefault(argparse.Action):
    def __init__(self, required=False, **kwargs):
        name = "WHACK_" + kwargs["option_strings"][0][2:].upper().replace("-", "_")
        default = os.environ.get(name)
        
        if default is not None:
            required=False
            
        super(type(self), self).__init__(default=default, required=required, **kwargs)
        
    def __call__(self, parser, namespace, values, option_string=None):
        print '%r %r %r' % (namespace, values, option_string)
        setattr(namespace, self.dest, values)

_commands = {
    "install": InstallCommand,
}
