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
from yay.context import RootContext

class Config(object):

    def __init__(self, special_term='yay'):
        self.special_term = special_term
        self.openers = Openers()
        self.clear()

    def load_uri(self, uri):
        self.load(self.openers.open(uri))

    def load(self, stream):
        data = Loader(stream, special_term=self.special_term).compose(self.mapping)
        self.mapping = data

    def clear(self):
        self.mapping = None

    def get(self):
        if not self.mapping:
            return {}
        return self.mapping.resolve(RootContext(self.mapping))

def load_uri(uri, special_term='yay'):
    c = Config(special_term)
    c.load_uri(uri)
    return c.get()

def load(stream, special_term='yay'):
    c = Config(special_term)
    c.load(stream)
    return c.get()

def dump(obj):
    return yaml.dump(obj, default_flow_style=False)

