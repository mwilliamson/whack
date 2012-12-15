import argparse
import os

def env_default(prefix):
    class EnvDefault(argparse.Action):
        def __init__(self, required=False, **kwargs):
            option_string = self._find_long_option_string(kwargs["option_strings"])
            
            name = prefix + "_" + option_string[2:].upper().replace("-", "_")
            default = os.environ.get(name)
            
            if default is not None:
                required=False
                
            super(type(self), self).__init__(default=default, required=required, **kwargs)
        
        def _find_long_option_string(self, option_strings):
            for option_string in option_strings:
                if option_string.startswith("--"):
                    return option_string
        
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values)
            
    return EnvDefault
            
    
