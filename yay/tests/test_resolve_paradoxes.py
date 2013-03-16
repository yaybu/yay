import unittest
from .base import parse, resolve
from yay import errors


class TestResolveParadoxes(unittest.TestCase):

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
        self.assertEqual(t.get("foo").as_int(), 1)

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

        self.assertEqual(t.get("out").get("foo").resolve(), "ok")

    def test_if_preventing_itself(self):
        """
        foo is 'bar', so select returns a dict with foo key
        but now foo is 'qux' so foo shouldn't have changed
        """
        t = parse("""
            bar: 1
            foo: {{ bar }}

            if foo:
                bar: 0
            """)

        self.assertEqual(t.get("bar").as_int(), 0)
        self.assertEqual(t.get("foo").as_int(), 0)

        self.assertRaises(errors.ParadoxError, t.resolve)


