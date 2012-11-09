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

from .base import TestCase

class TestJinja(TestCase):

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

    def test_value_of_sibling(self):
        source = """
            foo:
              bar: hello
            foo j2:
              % if foo.bar == 'hello':
              box: world
              % endif
            """
        self.assertResolves(source, {"foo":{"bar":"hello","box":"world"}})


