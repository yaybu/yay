# Copyright 2011 Isotoma Limited
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

# Dogfood tests are tests from real-world scenarios and test previous failure modes or specific fixes and feature scenarios

import unittest
from yay import parser
from yay.ast import Root
from yay import ast

# FIXME: This is duplicated in test_resolve

p = parser.Parser(debug=0)

class MockRoot(Root):

    def __init__(self, node):
        super(MockRoot, self).__init__(node)
        self.data = {}

    def add(self, key, value):
        self.data[key] = value

    def parse(self, path):
        return p.parse(self.data[path])

def parse(value, **kwargs):
    root = MockRoot(p.parse(value))
    for k, v in kwargs.items():
        root.add(k, v)
    return root

def resolve(value, **kwargs):
    return parse(value, **kwargs).resolve()


class TestDogfoodScenarios(unittest.TestCase):

    def test_range(self):
        res = resolve("""
            upper: 3
            foo: {{ range(upper) }}
            bar: {{ range(1, upper+1) }}
            """)
        self.assertEqual(res['foo'], [0, 1, 2])
        self.assertEqual(res['bar'], [1, 2, 3])

    def test_replace(self):
        res = resolve("""
            teststring: foo bar baz
            replacedstring: {{ replace(teststring, " ", "-") }}
            """)
        self.assertEqual(res['replacestring'], 'foo-bar-baz')

    def test_extend_lookup(self):
        """
        This test has 3 sections - a, b, c
        The parse will create 3 YayDicts and then merge c into b, then b into a
        If the merge is naive then it will cause predecessors to be lost.
        You can't just do v.predecessor, instead you need to find the tip of the predecessor ancestry
        """
        res = resolve("""
            foo:
                a: 1
                b: 1
                c: 1

            bar: {{ foo }}

            bar:
                d: 1

            """)
        self.assertEqual(res['bar']['a'], 1)
        self.assertEqual(res['bar']['d'], 1)

    def test_extend_lookup_lazier(self):
        """
        This test exists as a counterpoint to ``test_extend_lookup`` as we
        notcied that it was key-order-sensitive
        """
        res = resolve("""
            bar: {{ foo }}

            foo:
                a: 1
                b: 1
                c: 1

            bar:
                d: 1
            """)
        self.assertEqual(res['bar']['a'], 1)
        self.assertEqual(res['bar']['d'], 1)


    def test_extend_list_with_variable(self):
        res = resolve("""
            someval: julian
            somelist: []
            extend somelist:
              - {{ someval }}
            """)
        self.assertEqual(res['somelist'], ['julian'])

    def test_nested_foreach(self):
        res = resolve("""
            project:
              - name: monkeys
                flavour: bob
                environments:
                  - name: staging
                    host: ririn
                  - name: production
                    host: cloud
              - name: badgers
                flavour: george
                environments:
                 - name: staging
                   host: ririn
                 - name: production
                   host: cloud

            test:
              % for project in project
                % for env in project.environments
                    name: {{ project.name }}
                    env: {{ env.name }}
            """)

        self.assertEqual(res['test'], [
            {'name': 'monkeys', 'env': 'staging'},
            {'name': 'monkeys', 'env': 'production'},
            {'name': 'badgers', 'env': 'staging'},
            {'name': 'badgers', 'env': 'production'},
            ])

    def test_magic_1(self):
        res = resolve("""
            % include foo, "magic_1_1"
            """,
            magic_1_1="""
            foo: magic_1_2
            """,
            magic_1_2="""
            bar: its a kind of magic
            """)
        self.assertEqual(res['bar'], 'its a kind of magic')

    def test_magic_2(self):
        res = resolve("""
            % include test
            test: magic_2_1
            """,
            magic_2_1="""
            lol: it works
            """)
        self.assertEqual(res['lol'], 'it works')

    def test_else(self):
        res = resolve("""
            foo:
                bar: 42
                wibble: 22
            bar: {{ foo.baz or foo.bar }}
            baz: {{ foo.baz or foo.qux or foo.bar }}
            qux: {{ foo.wibble or foo.baz }}
            """)
        self.assertEqual(res['bar'], 42)
        self.assertEqual(res['baz'], 42)
        self.assertEqual(res['qux'], 22)

    def test_else_empty_list(self):
        res = resolve("""
            foo: {{ a or [] }}
            """)
        self.assertEqual(res['foo'], [])

    def test_else_empty_dict(self):
        res = resolve("""
            foo: {{ a or {} }}
            """)
        self.assertEqual(res['foo'], {})

    def test_else_string(self):
        res = resolve("""
            foo: {{ a or "foo" }}
            """)
        self.assertEqual(res['foo'], "foo")

    def test_else_include(self):
        res = resolve("""
            % include (a or "foo") + "_inc"
            """,
            foo_inc="hello:world")
        self.assertEqual(res['foo'], 'hello')

    def test_for_emit_dict(self):
        res = resolve("""
            foolist:
              - name: john
                age: 28
              - name: simon
                age: 41
              - name: sandra
                age: 47

            bar:
                maxage: 40

            baz:
                % for p in foolist if p.age < bar.maxage
                    - nameage: {{p.name}}{{p.age}}
                      agename: {{p.age}}{{p.name}}
            """)
        self.assertEqual(res['baz'], [{'nameage': 'john28', 'agename': '28john'}])

    def test_for_if_1(self):
        res = resolve("""
            nodes:
              - name: foo
              - name: baz
              - name: 5

            test:
                % for node in nodes if node.name == 5
                    - {{node}}
            """)
        self.assertEqual(res['test'], [{'name': 5}])

    def test_for_if_2(self):
        res = resolve("""
            nodes:
              - name: foo
              - name: baz
              - name: 5

            foo: foo

            test:
                % for node in nodes if node.name == foo
                    - {{node}}
            """)
        self.assertEqual(res['test'], [{'name': 'foo'}])

