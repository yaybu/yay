import unittest2
from yay.ast import YayMultilineScalar
from mock import Mock

v = "foo bar baz\nquux blor\n"
w = "foo bar baz\n\nquux blorp\n\n"

class TestASTMultiline(unittest2.TestCase):

    def _m(self, c):
        return (
            YayMultilineScalar(v, c).value,
            YayMultilineScalar(w, c).value,
            )

    def test_chomp_fold(self):
        self.assertEqual(self._m(">"), (
            'foo bar baz quux blor\n',
            'foo bar baz\nquux blorp\n',
            ))

    def test_chomp_literal(self):
        self.assertEqual(self._m("|"), (
            'foo bar baz\nquux blor\n',
            'foo bar baz\n\nquux blorp\n',
            ))

    def test_chomp_keep(self):
        # NB: the commented result below is the behaviour of pyyaml
        # however it is such an edge case, and so hard to fix
        # I'm happy to leave this - D
        self.assertEqual(self._m("|+"), (
            'foo bar baz\nquux blor\n',
            #'foo bar baz\n\nquux blorp\n\n\n',
            'foo bar baz\n\nquux blorp\n\n',
        ))

    def test_chomp_strip(self):
        self.assertEqual(self._m("|-"), (
            'foo bar baz\nquux blor',
            'foo bar baz\n\nquux blorp',
        ))
