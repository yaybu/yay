# Copyright 2013 Isotoma Limited
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

from .base import parse, resolve, TestCase
from yay import errors


class TestResolveParadoxes(TestCase):

    """
    Because of the lazily evaluated nature of yay there are various scenarios
    where a situation similar to the grandfather paradox occurs.

    Conditionals might alter variables that the conditional depend on.

    This would lead to inconsistent state, and thus is considered a critical
    error.
    """

    def test_include_preventing_itself(self):
        """
        foo is 1, 'example' is included
        If 'example' is included, then foo is 0
        So 'example' shouldn't be included
        """
        t = parse("""
                foo: 1
                include "example" if foo else []
                """,
                example="""
                foo: 0
                """)
        self.assertRaises(errors.ParadoxError, t.resolve)

    def test_include_preventing_itself_but_overriden(self):
        """
        This should work as foo: is not masked by an import
        """
        t = parse("""
                include "example" if foo else []
                foo: 1
                """,
                example="""
                foo: 0
                """)
        self.assertEqual(t.get_key("foo").as_int(), 1)

    def test_select_preventing_itself(self):
        """
        foo is 'bar', so select returns a dict with foo key
        but now foo is 'qux' so foo shouldn't have changed
        """
        t = parse("""
            out:
                foo: bar

            out:
                select out.foo:
                    bar:
                        foo: qux
            """)

        self.assertRaises(errors.ParadoxError, t.resolve)

    def test_select_preventing_itself_overriden(self):
        """
        foo is 'bar', so select returns a dict with foo key
        but now foo is 'qux' so foo shouldn't have changed
        """
        t = parse("""
            out:
                foo: bar

            out:
                select out.foo:
                    bar:
                        foo: qux

            out:
                foo: ok
            """)

        self.assertEqual(t.get_key("out").get_key("foo").resolve(), "ok")

    def test_if_preventing_itself(self):
        """
        bar is set to 0 when foo is 1, but as foo is only 1 when bar is 1..
        """
        t = parse("""
            bar: 1
            foo: {{ bar }}

            if foo:
                bar: 0
            """)

        self.assertRaises(errors.ParadoxError, t.resolve)

    def test_if_preventing_itself_overriden(self):
        """ This shouldn't be considered inconsistent either """
        t = parse("""
            bar: 1
            foo: {{ bar }}

            if foo:
                bar: 0

            bar: 1
            """)

        self.assertEqual(t.get_key("bar").resolve(), 1)

    def test_include_var_changes_in_include(self):
        t = parse("""
            lol: foo
            include lol
            """,
            foo="""
            lol: bar
            """,
            bar="""
            never: ever
            """)

        self.assertRaises(errors.ParadoxError, t.get_key, "never")

    def test_include_var_changes_in_include_overidden(self):
        t = parse("""
            lol: foo
            include lol
            lol: bar
            """,
            foo="""
            lol: bar
            """,
            bar="""
            never: ever
            """)

        self.assertEqual(t.get_key("never").resolve(), "ever")

    def test_paradoxical_directives_predecessor(self):
        """ Exercise looking up predecessors of Stanza/Directive nodes, but in a paradox situation """

        t = parse("""
            lol: foo

            if lol == 'foo':
                bar: baz

            if bar == 'baz':
                lol: zinga
            """)

        self.assertRaises(errors.ParadoxError, t.get_key, "lol")


class TestSearchPathParadoxes(TestCase):

    def test_searchpath_cant_change(self):
        self._add("mem://foodir/example2.yay", """
            foo: bar
            """)
        self._add("mem://bardir/example.yay", """
            yay:
                searchpath:
                  - {{ 'mem://foodir/' }}
            """)
        self.assertRaises(errors.ParadoxError, self._resolve, """
            yay:
                searchpath:
                  - {{ 'mem://bardir/' }}
            include "example.yay"
            include "example2.yay"
            """)

    def test_searchpath_cant_change_2(self):
        self._add("mem://foodir/example2.yay", """
            foo: bar
            """)
        self._add("mem://bardir/example.yay", """
            yay:
                searchpath:
                  - {{ 'mem://foodir/' }}
            """)
        self.assertRaises(errors.ParadoxError, self._resolve, """
            yay:
                searchpath:
                  - {{ 'mem://bardir/' }}
            include "example.yay"
            include "example2.yay"
            """)
