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

from yay import parser
from yay.errors import UnexpectedSymbolError, EOLParseError, EOFParseError
from .base import bare_parse as parse
from .base import TestCase


class TestParserErrors(TestCase):

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

    def test_multiline_if(self):
        self._r("Unexpected ':'.*line 4", """
        x: 1

        if x == \
            :
            - a
        """)
