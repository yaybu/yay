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

from yay.openers import Openers
from yay import errors
from yay import parser
from yay import ast


class Config(ast.Root):

    def __init__(self, special_term='yay', searchpath=None, config=None):
        self.special_term = special_term
        self.builtins = {}
        self.node = ast.NoPredecessorStandin()
        self.setup_openers(searchpath)

    def setup_openers(self, searchpath):
        self.openers = Openers(searchpath=searchpath)

    def load_uri(self, uri):
        __context__ = "Loading URI %s" % uri
        return self.load(self.openers.open(uri), uri)

    def load(self, stream, name="<Unknown>", secret=False):
        __context__ = "Loading stream %s. secret=%s." % (name, secret)
        p = parser.Parser()
        node = p.parse(stream.read(), source=name)
        node.parent = self
        mda = node
        while mda.predecessor and not isinstance(mda.predecessor, ast.NoPredecessorStandin):
            mda = mda.predecessor
        mda.predecessor = self.node
        self.node = node

    def add(self, data):
        if not isinstance(data, dict):
            raise errors.ProgrammingError("You must pass a dictionary to Config.add")
        bound = ast.bind(data)
        bound.parent = self
        bound.predecessor = self.node
        self.node = bound

    def get_context(self, key):
        try:
            return super(Config, self).get_context(key)
        except errors.NoMatching:
            if not key in self.builtins:
                raise
            return self.builtins[key]

    def clear(self):
        self.node = None

    def resolve(self):
        __context__ = "Performing full resolve"
        if not self.node:
            return {}
        return self.node.resolve()

    get = resolve

    def lookup(self, key):
        """
        Returns an object which can be resolved to a key on the current
        document
        """
        l = ast.Identifier(key)
        l.parent = self
        l.anchor = None
        return l


def load_uri(uri, special_term='yay'):
    c = Config(special_term)
    c.load_uri(uri)
    return c.resolve()

def load(stream, special_term='yay', secret=False):
    c = Config(special_term)
    c.load(stream, secret)
    return c.resolve()


