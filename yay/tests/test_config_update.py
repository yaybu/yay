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


import unittest
from yay.config import Config

class TestConfigUpdate(unittest.TestCase):

    def test_simple_update(self):
        c = Config()
        c.load("""
            foo: 1
            bar: 2
            baz: 3
            """)

        self.failUnless('foo' in c.get().keys())

    def test_simple_replace(self):
        c = Config()
        c.load("""
            foo: 1
            bar: 2
            baz: 3
            """)
        c.load("""
            foo: 3
            qux: 1
            """)

        self.failUnlessEqual(c.get()['foo'], 3)
        self.failUnlessEqual(c.get()['bar'], 2)
        self.failUnlessEqual(c.get()['qux'], 1)

    def test_nested_map_update(self):
        c = Config()
        c.load("""
            foo:
                foo: 1
                bar: 2
            bar: 2
            """)
        c.load("""
            foo:
                foo: 2
                baz: 3
            baz: 3
            """)

        self.failUnlessEqual(c.get()['foo']['foo'], 2)
        self.failUnlessEqual(c.get()['foo']['bar'], 2)
        self.failUnlessEqual(c.get()['foo']['baz'], 3)
        self.failUnlessEqual(c.get()['baz'], 3)

    def test_list(self):
        c = Config()
        c.load("""
            foo:
                - 1
                - 2
                - 3
            """)

        self.failUnlessEqual(c.get()['foo'], [1, 2, 3])

    def test_list_append(self):
        c = Config()

        c.load("""
            foo:
                - 1
                - 2
                - 3
            foo.append:
                - 4
                - 5
                - 6
            """)
        self.failUnlessEqual(c.get()['foo'], [1,2,3,4,5,6])

    def test_list_remove(self):
        c = Config()
        c.load("""
            foo:
                - 1
                - 2
                - 3
            foo.remove:
                - 1
                - 2
                - 3
                - 5
            """)

        self.failUnlessEqual(c.get()['foo'], [])

