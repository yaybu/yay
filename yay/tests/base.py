# Copyright 2012 Isotoma Limited
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

import unittest2
from yay import parser, ast, config
from yay.openers.base import MemOpener
import StringIO


class MockRoot(ast.Root):

    def __init__(self, node):
        super(MockRoot, self).__init__(node)
        self.data = {}

    def add(self, key, value):
        self.data[key] = value

    def _parse_uri(self, path):
        p = parser.Parser()
        return p.parse(self.data[path], debug=0)

def bare_parse(value):
    try:
        import yay.parsetab
        reload(yay.parsetab)
    except ImportError:
        pass
    p = parser.Parser()
    return p.parse(value, debug=False)

def parse(value, root=MockRoot, **kwargs):
    r = root(bare_parse(value))
    for k, v in kwargs.items():
        r.add(k, v)
    return r

def resolve(value, root=MockRoot, **kwargs):
    r = parse(value, root, **kwargs)
    return r.resolve()


class TestCase(unittest2.TestCase):

    builtins = None

    def setUp(self):
        self.addCleanup(MemOpener.reset)

    def _add(self, key, data):
        MemOpener.add(key, data)

    def _parse(self, source, labels=()):
        from yay.openers.base import Openers, SearchpathFromGraph
        class Config(config.Config):
            def setup_openers(self, searchpath):
                self.add({"yay": {"searchpath": searchpath or []}})
                self.openers = Openers(searchpath=SearchpathFromGraph(self.yay.searchpath))
        c = Config()
        c.builtins = self.builtins or {}
        c.load(StringIO.StringIO(source), labels=labels)
        return c

    def _resolve(self, source):
        return self._parse(source).resolve()

    def assertResolves(self, source, expected):
        self.assertEqual(self._resolve(source), expected)

