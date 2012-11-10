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

from .base import TestCase

class TestJinja(TestCase):

    def test_simple_variables(self):
        source = """
            foo: bye bye
            bar: {{ foo }} world
            foo: hello
            """
        self.assertResolves(source, {"foo": "hello", "bar": "hello world"})

    def test_simple_true(self):
        source = """
            foo:
              bar: hello
            foo j2:
              % if True
              bar: world
              % endif
            """
        self.assertResolves(source, {"foo":{"bar":"world"}})

    def test_simple_false(self):
        source = """
            foo:
              bar: hello
            foo j2:
              qux: :)
              % if False
              bar: world
              % endif
            """
        self.assertResolves(source, {"foo":{"bar":"hello","qux": ":)"}})

    def test_use_of_keys(self):
        source = """
            foo:
              bar: hello
            baz j2:
              % if foo.bar == 'hello'
              bar: world
              % endif
            """
        self.assertResolves(source, {"foo":{"bar":"hello"},"baz":{"bar":"world"}})

    #def test_use_of_sibling_keys(self):
    #    source = """
    #        foo:
    #          bar: hello
    #        foo j2:
    #          % if foo.bar == 'hello':
    #          box: world
    #          % endif
    #        """
    #    self.assertResolves(source, {"foo":{"bar":"hello","box":"world"}})


    def test_for_where_in_list(self):
        source = """
            list:
              - dog
              - cat
              - badger

            list2:
              - dog
              - mouse

            res1 j2:
              % for animal in list2 if animal in list
              - {{ animal }}
              % endfor
            """
        self.assertResolves(source, {
            "list": ["dog","cat","badger"],
            "list2": ["dog", "mouse"],
            "res1": ["dog"],
            })

    def test_for_on_sequence(self):
        source = """
            foo:
              - a
            qux:
              % for row in foo
              - {{ row }}
              % endfor
            """
        self.assertResolves(source, {"foo":["a"],"qux":["a"]})

    def test_for_on_extend(self):
        source = """
            foo:
              - a
            foo extend:
              - 1
            foo extend:
              - x
            bar j2:
              % for baz in foo
              - {{ baz }}
              % endfor
            """
        self.assertResolves(source, {"foo":["a","1","x"], "bar": ["a","1","x"]})

