import unittest2
from yay import parser
from yay.errors import UnexpectedSymbolError, EOLParseError, EOFParseError
from .base import bare_parse as parse

class TestParserErrors(unittest2.TestCase):

    def _r(self, re, src):
        self.assertRaisesRegexp(UnexpectedSymbolError, re, parse, src)

    def _eol(self, src):
        self.assertRaises(EOLParseError, parse, src)

    def test_bad_identifier_template(self):
        self._r("^Unexpected identifier.*line 2, column 18", """
        x: {{ a b c }}
        """)

    def test_missing_close_brace(self):
        self._eol("""
        x: {{a
        y: z
        """)

    def test_missing_open_brace(self):
        # not an error right now, is interpreted as a value
        res = parse("""
        x: a}}
        y: z
        """)

    def test_use_of_new(self):
        res = self._r("Unexpected 'new'", """
        extend new:
           - blah
        """)

    def test_use_of_extend(self):
        res = self._r("Unexpected 'extend'", """
        extend extend:
           - blah
        """)

    def test_broken_list(self):
        self._eol("""
        a:
          - foo
          bar
          - baz
        """)

    def test_empty_select_atom(self):
        self._r("Unexpected ':'", """
        select:
            x:
                - foo
        """)


    def test_empty_select_clause(self):
        self._r("Unexpected value", """
        select x:

        x: y
        """)

    def test_new_missing_symbol(self):
        self._r("Unexpected 'as'", """
        new as z:
            y: z
        """)


