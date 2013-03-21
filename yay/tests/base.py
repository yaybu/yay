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

import unittest
from yay import parser
from yay import ast

class MockRoot(ast.Root):

    def __init__(self, node):
        super(MockRoot, self).__init__(node)
        self.data = {}

    def add(self, key, value):
        self.data[key] = value

    def parse(self, path):
        p = parser.Parser()
        return p.parse(self.data[path], debug=0)

def bare_parse(value):
    try:
        import yay.parsetab
        reload(yay.parsetab)
    except ImportError:
        pass
    p = parser.Parser()
    return p.parse(value)

def parse(value, **kwargs):
    root = MockRoot(bare_parse(value))
    for k, v in kwargs.items():
        root.add(k, v)
    return root

def resolve(value, **kwargs):
    root = parse(value, **kwargs)
    return root.resolve()


class TestCase(unittest.TestCase):

    def _parse(self, source):
        return parse(source)

    def _resolve(self, source):
        return self._parse(source).resolve()

    def assertResolves(self, source, expected):
        self.assertEqual(self._resolve(source), expected)

