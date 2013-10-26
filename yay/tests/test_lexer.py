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

import types
from yay.lexer import Lexer
from yay.tests.base import TestCase
from ply import lex
from yay.errors import WhitespaceError


# ply works great but the implementation is a bit fugly

def lt__repr__(self):
    return "<%s(%r)>" % (self.type, self.value)


def lt__nonzero__(self):
    # work around some evil code in PLY
    return True


def lt__eq__(self, other):
    """ Used in tests only """
    if isinstance(other, type("")):
        if self.type == other and self.value == other:
            return True
    elif not isinstance(other, type(self)):
        return False
    else:
        if self.type == other.type and self.value == other.value:
            return True
    return False


def lt__ne__(self, other):
    return not self == other

lex.LexToken.__repr__ = lt__repr__
lex.LexToken.__nonzero__ = lt__nonzero__
lex.LexToken.__eq__ = lt__eq__
lex.LexToken.__ne__ = lt__ne__


def t(name, value=None, lineno=0, lexpos=0, orig=None):
    tok = lex.LexToken()
    tok.type = name
    tok.value = value
    tok.lineno = lineno
    tok.lexpos = lexpos
    tok.orig = orig
    return tok

newline = t('NEWLINE', '\n')
indent = t('INDENT', None)
dedent = t('DEDENT', None)
emptydict = t('EMPTYDICT', '{}')
emptylist = t('EMPTYLIST', '[]')
ldbrace = t('LDBRACE', '{{')
rdbrace = t('RDBRACE', '}}')
hyphen = t('HYPHEN', '-')
plus = t('+', '+')
colon = t('COLON', ':')


def value(x):
    return t('VALUE', x)


def identifier(x):
    return t('IDENTIFIER', x)


def line(x):
    return t('LINE', x)


class TestLexer(TestCase):

    def _lex(self, value):
        l = Lexer(debug=1)
        l.input(value)
        return list(l)

    def show_error(self, x, y):
        compar = []
        for a, b in map(lambda *z: z, x, y):
            if a == b:
                compar.append("     %-20r %-20r" % (a, b))
            else:
                compar.append(">    %-20r %-20r" % (a, b))
        return "\n".join(compar)

    def compare(self, x, y):
        """ Compare two lists of ts """
        if isinstance(x, types.GeneratorType):
            x = list(x)
        x.pop(0)
        if len(x) != len(y):
            raise self.failureException(
                "Token lists are of different lengths:\n%s" % self.show_error(x, y))
        for a, b in zip(x, y):
            if a != b:
                raise self.failureException(
                    "Tokens differ:\n%s" % self.show_error(x, y))

    # Base YAY tests

    def test_simplest(self):
        self.compare(self._lex("""a: b"""), [
            value('a'), colon, value('b')
        ])

    def test_list(self):
        result = self._lex("""
        a:
          - b
          - c
          - d
        """)
        self.compare(result, [
            value('a'), colon, newline,
            indent,
            hyphen, value('b'), newline,
            hyphen, value('c'), newline,
            hyphen, value('d'), newline,
            dedent,
        ])

    def test_simple_indent(self):
        result = self._lex("""
        a:
          b: c
        """)
        self.compare(result, [
            value('a'), colon, newline,
            indent,
            value('b'), colon, value('c'), newline,
            dedent,
        ])

    def test_list_of_multikey_dicts(self):
        result = self._lex("""
            a:
              - b
              - c: d
                e: f
              - g
              """)
        self.compare(result, [
            value('a'), colon, newline,
            indent,
            hyphen, value('b'), newline,
            hyphen, value('c'), colon, value('d'), newline,
            indent,
            value('e'), colon, value('f'), newline,
            dedent,
            hyphen, value('g'), newline,
            dedent,
        ])

    def test_list_of_dicts(self):
        self.compare(self._lex("""
            a:
              - b
              - c: d
              - e
        """), [
            value('a'), colon, newline,
            indent,
            hyphen, value('b'), newline,
            hyphen, value('c'), colon, value('d'), newline,
            hyphen, value('e'), newline,
            dedent,
        ])

    def test_initial1(self):
        self.compare(self._lex("""
               a: b
               c:
                 d: e
            """), [
            value('a'), colon, value('b'), newline,
            value('c'), colon, newline,
            indent,
            value('d'), colon, value('e'), newline,
            dedent,
        ])

    def test_emptydict(self):
        self.compare(self._lex("""
            a: {}
        """), [
            value('a'), colon, emptydict, newline,
        ])

    def test_emptylist(self):
        self.compare(self._lex("""
            a: []
        """), [
            value('a'), colon, emptylist, newline,
        ])

    def test_comments(self):
        self.compare(self._lex("""
            # example
            a: b
            c:
              - d
              # foo
              - e
            """), [
            value('a'), colon, value('b'), newline,
            value('c'), colon, newline,
            indent,
            hyphen, value('d'), newline,
            hyphen, value('e'), newline,
            dedent,
        ])

    def test_sample2(self):
        self.compare(self._lex("""
        a:
            b: c
            e:
                - f
                - g
            h:
                i: j
        """), [
            value('a'), colon, newline,
            indent,
            value('b'), colon, value('c'), newline,
            value('e'), colon, newline,
            indent,
            hyphen, value('f'), newline,
            hyphen, value('g'), newline,
            dedent,
            value('h'), colon, newline,
            indent,
            value('i'), colon, value('j'), newline,
            dedent,
            dedent
        ])

    def test_sample1(self):
        self.compare(self._lex("""
            key1: value1

            key2: value2

            key3:
              - item1
              - item2
              - item3

            key4:
                key5:
                    key6: key7
        """), [
            value('key1'), colon, value('value1'), t('NEWLINE', '\n\n'),
            value('key2'), colon, value('value2'), t('NEWLINE', '\n\n'),
            value('key3'), colon, newline,
            indent,
            hyphen, value('item1'), newline,
            hyphen, value('item2'), newline,
            hyphen, value('item3'), t('NEWLINE', '\n\n'),
            dedent,
            value('key4'), colon, newline,
            indent,
            value('key5'), colon, newline,
            indent,
            value('key6'), colon, value('key7'), newline,
            dedent,
            dedent,
        ])

    # def test_multiline(self):
        # self.compare(self._lex("""
            # foo: |
               # bar
               # baz
               # quux
            # bar: |
               # x y z
               # a b c
        #"""), [])

    # def test_deep_multiline_file_end(self):
        # self.compare(self._lex("""
            # foo:
                # bar: |
                    # quux
        #"""), [])

    # def test_multiline_template(self):
        # self.compare(self._lex("""
        # foo: |
          # bar
          # baz
          #{{quux}}
        #"""), [

        #])

    def test_extend(self):
        self.compare(self._lex("""
        extend foo:
            - baz
            - quux
        """), [
            t('EXTEND', 'extend'), value('foo'), colon, newline,
            indent,
            hyphen, value('baz'), newline,
            hyphen, value('quux'), newline,
            dedent,

        ])

    # command mode tests

    def test_command(self):
        result = self._lex("""
            include 'foo.yay'
        """)
        self.compare(result, [
            t('INCLUDE', 'include'),
            t('STRING', 'foo.yay'),
            newline,
        ])

    def test_include_levels(self):
        result = self._lex("""
        a:
            include 'foo.yay'
        """)
        self.compare(result, [
            value('a'), colon, newline,
            indent,
            t('INCLUDE', 'include'),
            t('STRING', 'foo.yay'),
            newline,
            dedent,
        ])

    def test_new(self):
        result = self._lex("""
            new Compute:
        """)
        self.compare(result, [
            t('NEW', 'new'), identifier('Compute'), t(':', ':'),
            newline,
        ])

    def test_new_as(self):
        result = self._lex("""
            new Provisioner as foo:
        """)
        self.compare(result, [
            t('NEW', 'new'), identifier('Provisioner'), t(
                'AS', 'as'), identifier('foo'), t(':', ':'), newline,
        ])

    def test_if(self):
        result = self._lex("""
            if selector == "hey":
                foo: 2
        """)
        self.compare(result, [
            t('IF', 'if'), identifier('selector'), t(
                'EQ', '=='), t('STRING', 'hey'), t(':', ':'),
            newline,
            indent, value('foo'), colon, value('2'), newline, dedent,
        ])

    def test_else(self):
        result = self._lex("""
        else:
        """)
        self.compare(result, [
            t('ELSE', 'else'), t(':', ':'), newline,
        ])

    def test_macro(self):
        result = self._lex("""
            macro foo:
                x: y
        """)
        self.compare(result, [
            t('MACRO', 'macro'), t('IDENTIFIER', 'foo'), t(':', ':'), newline,
            indent, value('x'), colon, value('y'), newline, dedent,
        ])

    def test_integer(self):
        result = self._lex("""
        set a = 2
        """)
        self.compare(result, [
            t('SET', 'set'),
            identifier('a'),
            t('=', '='),
            t('INTEGER', 2),
            newline,
        ])

    def test_addition(self):
        result = self._lex("""
        set a = 2+2
        """)
        self.compare(result, [
            t('SET', 'set'),
            identifier('a'),
            t('=', '='),
            t('INTEGER', 2),
            t('+', '+'),
            t('INTEGER', 2),
            newline,
        ])

    def test_leading_command(self):
        self.compare(self._lex("""
            include 'foo.yay'

            a: b
            """), [
            t('INCLUDE', 'include'), t('STRING', 'foo.yay'),
            t('NEWLINE', '\n\n'),
            value('a'), colon, value('b'), newline,
        ])

    # template tests

    def test_single_brace(self):
        self.compare(self._lex("""
            foo: hello {world}
        """), [
            value('foo'), colon,
            value('hello {world}'),
            newline,
        ])

    def test_template(self):
        self.compare(self._lex("foo: {{bar}}"), [
            value('foo'), colon,
            t('LDBRACE', '{{'),
            t('IDENTIFIER', 'bar'),
            t('RDBRACE', '}}'),
        ])

    def test_complex_expressions_in_templates(self):
        self.compare(self._lex("""
        a: this {{a+b+c}} is {{foo("bar")}} hard
        """), [
            value('a'), colon,
            value('this '),
            ldbrace,
            identifier('a'),
            plus,
            identifier('b'),
            plus,
            identifier('c'),
            rdbrace,
            value(' is '),
            ldbrace,
            identifier('foo'),
            t('(', '('),
            t('STRING', 'bar'),
            t(')', ')'),
            rdbrace,
            value(' hard'),
            newline,
        ])

    def test_template_in_listitem(self):
        self.compare(self._lex("""
        foo:
          - a
          - {{bar}}
          - c
        """), [
            value('foo'), colon, newline,
            indent,
            hyphen, value('a'), newline,
            hyphen, ldbrace, t('IDENTIFIER', 'bar'), rdbrace, newline,
            hyphen, value('c'), newline,
            dedent,
        ])

    def test_braces(self):
        self.compare(self._lex("""
        foo: a{b}
        """), [
            value('foo'), colon, value('a{b}'), newline
        ])

    def test_simple_dict_space(self):
        self.compare(self._lex("""
        a : b
        """), [
            value('a'), colon, value('b'), newline
        ])

    def test_multiline_fold_simple(self):
        # indentation here is intentional
        self.compare(self._lex("""
a: >
  foo bar baz
  quux quuux

b: c
"""), [
            value('a'), colon,
            t('MULTILINE', '>'),
            value('foo bar baz'),
            newline,
            value('quux quuux'),
            t('NEWLINE', '\n\n'),
            t('MULTILINE_END'),
            newline,
            value('b'), colon, value('c'), newline,
        ])

    def test_multiline_inplace(self):
        self.compare(self._lex("""
        a: >
          foo bar baz
          quux quuux

        b: c
        """), [
            value('a'), colon,
            t('MULTILINE', '>'),
            value('foo bar baz'),
            newline,
            value('quux quuux'),
            t('NEWLINE', '\n\n'),
            t('MULTILINE_END'),
            newline,
            value('b'), colon, value('c'), newline
        ])

    def test_multiline_fold_template(self):
        self.compare(self._lex("""
        a: >
          foo {{bar}} baz
          {{quux}} quuux
        """), [
            value('a'), colon,
            t('MULTILINE', '>'),
            value('foo '), ldbrace, t('IDENTIFIER', 'bar'), rdbrace,
            value(' '), value('baz'),
            newline,
            ldbrace, t('IDENTIFIER', 'quux'), rdbrace, value(
                ' '), value('quuux'),
            newline,
            t('MULTILINE_END'),
            newline,
        ])

    def test_multiline_fold(self):
        self.compare(self._lex("""
        a: >
          foo bar baz

          quux quuux
        """), [
            value('a'), colon,
            t('MULTILINE', '>'),
            value('foo bar baz'),
            t('NEWLINE', '\n\n'),
            value('quux quuux'),
            newline,
            t('MULTILINE_END'),
            newline,
        ])

    def test_multiline_literal(self):
        self.compare(self._lex("""
        a: |
          foo bar baz

          quux quuux


        """), [
            value('a'), colon,
            t('MULTILINE', '|'),
            value('foo bar baz'),
            t('NEWLINE', '\n\n'),
            value('quux quuux'),
            t('NEWLINE', '\n\n\n'),
            t('MULTILINE_END'),
            newline,
        ])

    def test_multiline_literal_complex(self):
        self.compare(self._lex("""
        a:
            b: |
                l1
                l2
            c: x
        d: e
        """), [
            value('a'),
            colon,
            newline,
            indent,
            value('b'),
            colon,
            t('MULTILINE', '|'),
            value('l1'),
            newline,
            value('l2'),
            newline,
            t('MULTILINE_END'),
            newline,
            value('c'),
            colon,
            value('x'),
            newline,
            dedent,
            value('d'),
            colon,
            value('e'),
            newline,
        ])

    def test_multiline_strip(self):
        self.compare(self._lex("""
        a: |-
          foo bar baz

          quux quuux


        """), [
            value('a'),
            colon,
            t('MULTILINE', '|-'),
            value('foo bar baz'),
            t('NEWLINE', '\n\n'),
            value('quux quuux'),
            t('NEWLINE', '\n\n\n'),
            t('MULTILINE_END'),
            newline,
        ])

    def test_multiline_strip_with_template(self):
        self.compare(self._lex("""
        a: |-
          foo bar baz

          quux {{ quux }}


        """), [
            value('a'), colon, t('MULTILINE', '|-'),
            value('foo bar baz'),
            t('NEWLINE', '\n\n'),
            value('quux '),
            ldbrace, identifier('quux'), rdbrace,
            t('NEWLINE', '\n\n\n'),
            t('MULTILINE_END'),
            newline
        ])

    def test_multiline_keep(self):
        self.compare(self._lex("""
        a: |+
          foo bar baz

          quux quuux


        """), [
            value('a'), colon,
            t('MULTILINE', '|+'),
            value('foo bar baz'),
            t('NEWLINE', '\n\n'),
            value('quux quuux'),
            t('NEWLINE', '\n\n\n'),
            t('MULTILINE_END'),
            newline,
        ])

    def test_python_line_continuation(self):
        self.compare(self._lex(r"""
        if x == y and \
           c == d:
             - x
        """), [
            t('IF', 'if'),
            identifier('x'),
            t('EQ', '=='),
            identifier('y'),
            t('AND', 'and'),
            identifier('c'),
            t('EQ', '=='),
            identifier('d'),
            t(':', ':'),
            newline,
            indent, hyphen, value('x'), newline, dedent,
        ])

    def test_yaml_line_continuation(self):
        self.compare(self._lex(r"""
        a: b \
        x: y
        """), [
            value('a'), colon, value('b \\'), newline,
            value('x'), colon, value('y'), newline,
        ])

    def test_quoted_values(self):
        self.compare(self._lex(r"""
        a: "b: c d"
        """), [
            value('a'), colon, value('b: c d'), newline,
        ])

    def test_templates_in_quotes(self):
        self.compare(self._lex(r"""
        a: "{{foo}}:{{bar}}"
        """), [
            value('a'), colon,
            ldbrace, identifier('foo'), rdbrace, value(':'),
            ldbrace, identifier('bar'), rdbrace,
            newline
        ])

    def test_colon_key_nospace(self):
        self.compare(self._lex(r"""
        a:b
        """), [value('a:b'), newline])

    def test_colon_key_space(self):
        self.compare(self._lex(r"""
        a: b
        """), [value('a'), colon, value('b'), newline])

    def test_colon_value_nospace(self):
        self.compare(self._lex(r"""
        a: b:c
        """), [value('a'), colon, value('b:c'), newline])

    def test_colon_value_nospace2(self):
        self.compare(self._lex(r"""
        a: b: c
        """), [value('a'), colon, value('b'), colon, value('c'), newline])

    def test_code_in_list(self):
        self.compare(self._lex(r"""
        a:
          - a
          - b
          for i in j:
            - {{i}}
          - c
        """), [value('a'), colon, newline,
               indent,
               hyphen, value('a'), newline,
               hyphen, value('b'), newline,
               t('FOR', 'for'), identifier('i'), t(
                   'IN', 'in'), identifier('j'), t(':', ':'), newline,
               indent,
               hyphen, ldbrace, identifier('i'), rdbrace, newline,
               dedent,
               hyphen, value('c'), newline,
               dedent
               ])

    def test_for_in_list_in_for(self):
        self.compare(self._lex("""
        a:
          for x in y:
            - a
            for i in j:
              - {{i}}
            - c
        """), [value('a'), colon, newline,
               indent,
               t('FOR', 'for'), identifier('x'), t(
                   'IN', 'in'), identifier('y'), t(':', ':'), newline,
               indent,
               hyphen, value('a'), newline,
               t('FOR', 'for'), identifier('i'), t(
                   'IN', 'in'), identifier('j'), t(':', ':'), newline,
               indent,
               hyphen, ldbrace, identifier('i'), rdbrace, newline,
               dedent,
               hyphen, value('c'), newline,
               dedent,
               dedent,
               ])

    def test_quote_corner_case(self):
        self.compare(self._lex("""
          a: - "{{x}}"
          b: "y"
          """), [value('a'), colon, value('- "'), ldbrace, identifier('x'), rdbrace, value('"'),
                 newline,
                 value('b'), colon, value('y'), newline,
                 ])

    def test_trailing_whitespace(self):
        self.compare(self._lex("a: b \n"""), [
                     value('a'), colon, value('b'), newline])

    def test_trailing_whitespace_before_template(self):
        self.compare(self._lex("a: b {{c}}"), [
            value('a'), colon, value('b '),
            ldbrace, identifier('c'), rdbrace])

    def test_inconsistent_indentation(self):
        self.assertRaises(WhitespaceError, self._lex, """
        a:
            b:
                c: d
              e: f
        """)
