import types

import yaml

from yay.loader import Loader
from yay.resolver import Resolver
from yay.ordereddict import OrderedDict
from yay.openers import Openers
from yay.actions import Actions

class Config(object):

    def __init__(self, special_term='yay'):
        self.special_term = special_term
        self.openers = Openers()
        self.actions = Actions()
        self._raw = {}

    def load_uri(self, uri):
        self.load(self.openers.open(uri))

    def load(self, stream):
        data = yaml.load(stream, Loader=Loader)

        special = data.get(self.special_term, None)
        if special:
            for uri in special.get('extends', []):
                self.load_uri(uri)

        self.update(data)

    def update(self, config):
        """
        Recursively update config with a dict
        """
        def recurse(src, target):
            for key, value in src.iteritems():
                if "." in key:
                    key, action = key.split(".")
                else:
                    action = "assign"

                if isinstance(value, dict):
                    if not isinstance(target, dict):
                        # Underlying config has something other than a dict. I.E we changed type in a child overlay
                        # Need to think more carefully about what to do here. Is this an error, or should we force the type
                        # to change (I think we should force the type to change)
                        raise ValueError("%s\n%s\n%s" % (key, target, value))
                    recurse(value, target.setdefault(key, {}))
                else:
                    target[key] = self.actions.run(action, target.get(key, None), value)

        recurse(config, self._raw)

    def clear(self):
        self._raw = {}

    def get(self):
        return Resolver(self._raw).resolve()

def load_uri(uri, special_term='yay'):
    c = Config(special_term)
    c.load_uri(uri)
    return c.get()

def load(stream, special_term='yay'):
    c = Config(special_term)
    c.load(stream)
    return c.get()

