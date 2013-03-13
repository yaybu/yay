
import unittest
import types
from yay.lexer import Lexer
from ply import lex


# ply works great but the implementation is a bit fugly

def lt__repr__(self):
    if self.value == '\n':
        return "<NEWLINE>"
    else:
        return "<%s(%s)>" % (self.type, self.value)

def lt__nonzero__(self):
    # work around some evil code in PLY
    return True

def lt__eq__(self, other):
    """ Used in tests only """
    if type(other) == type(""):
        if self.type == other and self.value == other:
            return True
    elif type(other) != type(self):
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

def key(x):
    return t('VALUE', x)

def value(x):
    return t('VALUE', x)

def identifier(x):
    return t('IDENTIFIER', x)

class TestLexer(unittest.TestCase):

    def _lex(self, value):
        l = Lexer(debug=0)
        l.input(value)
        return list(l)

    def show_error(self, x, y):
        compar = []
        for a, b in map(None, x, y):
            if a == b:
                compar.append("     %-20r %-20r" % (a, b))
            else:
                compar.append(">    %-20r %-20r" % (a, b))
        return "\n".join(compar)

    def compare(self, x, y):
        """ Compare two lists of ts """
        if type(x) == types.GeneratorType:
            x = list(x)
        if len(x) != len(y):
            raise self.failureException("Token lists are of different lengths:\n%s" % self.show_error(x, y))
        for a, b in zip(x,y):
            if a != b:
                raise self.failureException("Tokens differ:\n%s" % self.show_error(x,y))

    ##### Base YAY tests

    def test_simplest(self):
        self.compare(self._lex("""a: b"""), [
        key('a'), colon, value('b')
        ])

    def test_list(self):
        result = self._lex("""
        a:
          - b
          - c
          - d
        """)
        self.compare(result, [
            key('a'), colon, newline,
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
            key('a'), colon, newline,
            indent,
                key('b'), colon, value('c'), newline,
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
        key('a'), colon, newline,
        indent,
            hyphen, value('b'), newline,
            hyphen, key('c'), colon, value('d'), newline,
            indent,
                key('e'), colon, value('f'), newline,
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
            key('a'), colon, newline,
            indent,
                hyphen, value('b'), newline,
                hyphen, key('c'), colon, value('d'), newline,
                hyphen, value('e'), newline,
            dedent,
            ])

    def test_initial1(self):
        self.compare(self._lex("""
               a: b
               c:
                 d: e
            """), [
                key('a'), colon, value('b'), newline,
                key('c'), colon, newline,
                indent,
                    key('d'), colon, value('e'), newline,
                dedent,
            ])

    def test_emptydict(self):
        self.compare(self._lex("""
            a: {}
        """), [
            key('a'), colon, emptydict, newline,
        ])

    def test_emptylist(self):
        self.compare(self._lex("""
            a: []
        """), [
            key('a'), colon, emptylist, newline,
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
                   t('COMMENT', '# example'),  newline,
                   key('a'), colon, value('b'), newline,
                   key('c'), colon, newline,
                   indent,
                   hyphen, value('d'), newline,
                   t('COMMENT', '# foo'), newline,
                   hyphen, value('e'), newline,
                   dedent,
            ])

    def test_sample2(self):
        self.compare(self._lex("""
        a:
            b:c
            e:
                - f
                - g
            h:
                i: j
        """), [
               key('a'), colon, newline,
               indent,
                key('b'), colon, value('c'), newline,
                key('e'), colon, newline,
                indent,
                    hyphen, value('f'), newline,
                    hyphen, value('g'), newline,
                dedent,
                key('h'), colon, newline,
                indent,
                    key('i'), colon, value('j'), newline,
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
               key('key1'), colon, value('value1'), t('NEWLINE', '\n\n'),
               key('key2'), colon, value('value2'), t('NEWLINE', '\n\n'),
               key('key3'), colon, newline,
               indent,
                   hyphen, value('item1'), newline,
                   hyphen, value('item2'), newline,
                   hyphen, value('item3'), t('NEWLINE', '\n\n'),
               dedent,
               key('key4'), colon, newline,
               indent,
                   key('key5'), colon, newline,
                   indent,
                       key('key6'), colon, value('key7'), newline,
                   dedent,
               dedent,
        ])

    #def test_multiline(self):
        #self.compare(self._lex("""
            #foo: |
               #bar
               #baz
               #quux
            #bar: |
               #x y z
               #a b c
        #"""), [])

    #def test_deep_multiline_file_end(self):
        #self.compare(self._lex("""
            #foo:
                #bar: |
                    #quux
        #"""), [])

    #def test_multiline_template(self):
        #self.compare(self._lex("""
        #foo: |
          #bar
          #baz
          #{{quux}}
        #"""), [

        #])

    def test_extend(self):
        self.compare(self._lex("""
        extend foo:
            - baz
            - quux
        """), [
               t('EXTEND', 'extend'), key('foo'), colon, newline,
               indent,
               hyphen, value('baz'), newline,
               hyphen, value('quux'), newline,
               dedent,

           ])

    ##### command mode tests

    def test_command(self):
        result = self._lex("""
            include 'foo.yay'
        """)
        self.compare(result, [
            t('INCLUDE', 'include'),
            t('STRING', 'foo.yay'),
            newline,
            ])

    def test_if(self):
        result = self._lex("""
            if selector == "hey":
                foo: 2
        """)
        self.compare(result, [
            t('IF', 'if'), identifier('selector'), t('EQ', '=='), t('STRING', 'hey'), t(':', ':'),
            newline,
            indent, key('foo'), colon, value('2'), newline, dedent,
            ])


    def test_macro(self):
        result = self._lex("""
            macro foo:
                x: y
        """)
        self.compare(result, [
            t('MACRO', 'macro'), t('IDENTIFIER', 'foo'), t(':', ':'), newline,
            indent, key('x'), colon, value('y'), newline, dedent,
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
                key('a'), colon, value('b'), newline,
                ])

    ##### template tests

    def test_single_brace(self):
        self.compare(self._lex("""
            foo: hello {world}
        """), [
               key('foo'), colon,
               value('hello '),
               t('{', '{'),
               value('world}'),
               newline,
           ])

    def test_template(self):
        self.compare(self._lex("foo: {{bar}}"), [
                key('foo'), colon,
                t('LDBRACE', '{{'),
                t('IDENTIFIER', 'bar'),
                t('RDBRACE', '}}'),
        ])

    def test_complex_expressions_in_templates(self):
        self.compare(self._lex("""
        a: this {{a+b+c}} is {{foo("bar")}} hard
        """), [
               key('a'), colon,
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
           key('foo'), colon, newline,
           indent,
               hyphen, value('a'), newline,
               hyphen, ldbrace, t('IDENTIFIER', 'bar'), rdbrace, newline,
               hyphen, value('c'), newline,
            dedent,
        ])

