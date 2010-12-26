
import yaml

from yay.loader import Loader
from yay.resolver import Resolver

class Config(object):

    def __init__(self):
        self._raw = {}

    def load(self, stream):
        data = yaml.load(stream, loader=Loader)
        self.update(data)

    def update(self, config):
        def recurse(src, target):
            for key, value in src.iteritems():
                if "." in key:
                    key, action = key.split(".")
                else:
                    action = "assign"

                if value is types.DictionaryType:
                    recurse(value, target.setdefault(key, {}))
                else:
                    target[key] = value

    def get(self):
        return Resolver(self._raw).resolve()
