# Copyright 2010-2011 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import yaml

from yay.loader import Loader
from yay.openers import Openers
from yay.composer import Composer
from yay.context import RootContext

class Config(object):

    def __init__(self, special_term='yay'):
        self.special_term = special_term
        self.openers = Openers()
        self.tt = Composer()

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
        self.tt.update(config)

    def clear(self):
        self.tt.root = None

    def get(self):
        if not self.tt.root:
            return {}
        return self.tt.root.resolve(RootContext(self.tt.root))

def load_uri(uri, special_term='yay'):
    c = Config(special_term)
    c.load_uri(uri)
    return c.get()

def load(stream, special_term='yay'):
    c = Config(special_term)
    c.load(stream)
    return c.get()

