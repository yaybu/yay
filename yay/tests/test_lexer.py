
import unittest
import types
from yay.lexer import Lexer, LexToken, identifier_re

t = LexToken

class TestLexer(unittest.TestCase):
    
    def _lex(self, value):
        l = Lexer()
        l.input(value)
        l.done()
        return list(l)
    
    def test_re(self):
        self.assertEqual(identifier_re.match("foo").group(), "foo")
        self.assertEqual(identifier_re.match("f9").group(), "f9")
    
    def test_parse_command(self):
        def p(l):
            return Lexer().parse_command(l)
        self.compare(p("+"), ['+'])
        self.compare(p("'foo'"), [t('LITERAL', "foo")])
        self.compare(p("('foo')"), ['(', t('LITERAL', "foo"), ')'])
        self.compare(p("a + 'foo'"), [t('IDENTIFIER', 'a'), '+', t('LITERAL', "foo")])
        self.compare(p("a+2"), [t('IDENTIFIER', 'a'), '+', t('LITERAL', 2)])
        self.compare(p("a<<5"), [t('IDENTIFIER', 'a'), t('LSHIFT', "<<"), t('LITERAL', 5)])
        self.compare(p("a<5"), [t('IDENTIFIER', 'a'), '<', t('LITERAL', 5)])
        self.compare(p("a and 5"), [t('IDENTIFIER', 'a'), t('AND', 'and'), t('LITERAL', 5)])
        self.compare(p("a andy 5"), [t('IDENTIFIER', 'a'), t('IDENTIFIER', 'andy'), t('LITERAL', 5)])
        self.compare(p("[1,2.0,'foo']"), ['[', t('LITERAL', 1), ',', t('LITERAL', 2.0), ',', t('LITERAL', "foo"), ']'])
    
    def test_whole_command(self):
        result = self._lex("""
        % include 'foo.yay'
        """)
        self.compare(result, [
            t('INDENT'),
            t('%', '%'),
            t('INCLUDE', 'include'),
            t('LITERAL', 'foo.yay'),
            t('DEDENT'),
            ])
            
    
    def compare(self, x, y):
        """ Compare two lists of ts """
        if type(x) == types.GeneratorType:
            x = list(x)
        if len(x) != len(y):
            raise self.failureException("Token lists are of different lengths: %r %r", (x, y))
        for a, b in zip(x,y):
            if a != b:
                raise self.failureException("Tokens %r %r differ" % (a,b))                
    
    def test_list_of_multikey_dicts(self):
        result = self._lex("""
            a: 
              - b
              - c: d
                e: f
              - g
              """)
        self.compare(result, [ t('INDENT'),
            t('KEY', 'a'),
            t('INDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'b'), t('DEDENT'),
                t('LISTITEM'),
                t('INDENT'),
                    t('KEY', 'c'), t('INDENT'), t('SCALAR', 'd'), t('DEDENT'),
                    t('KEY', 'e'), t('INDENT'), t('SCALAR', 'f'), t('DEDENT'),
                t('DEDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'g'), t('DEDENT'),
            t('DEDENT'),
            t('DEDENT'), ])

    def test_list_of_dicts(self):
        self.compare(self._lex("""
            a:
              - b
              - c: d
              - e
        """), [ t('INDENT'),
            t('KEY', 'a'),
            t('INDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'b'), t('DEDENT'),
                t('LISTITEM'),
                t('INDENT'),
                    t('KEY', 'c'), t('INDENT'), t('SCALAR', 'd'), t('DEDENT'),
                t('DEDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'e'), t('DEDENT'),
            t('DEDENT'),
        t('DEDENT'), ])
    
    def test_initial1(self):
        self.compare(self._lex("""
               a: b
               c: 
                 d: e
            """), [ t('INDENT'),
            t('KEY', 'a'), t('INDENT'), t('SCALAR', 'b'), t('DEDENT'),
            t('KEY', 'c'),
            t('INDENT'),
                t('KEY', 'd'), t('INDENT'), t('SCALAR', 'e'), t('DEDENT'),
            t('DEDENT'),
            t('DEDENT'), ])
    
    def test_emptydict(self):
        self.compare(self._lex("a: {}"), [ t('INDENT'),
            t('KEY', 'a'), t('INDENT'), t('EMPTYDICT', ), t('DEDENT'),
            t('DEDENT'), ])
        
    def test_emptylist(self):
        self.compare(self._lex("a: []"), [ t('INDENT'),
            t('KEY', 'a'), t('INDENT'), t('EMPTYLIST'), t('DEDENT'),
            t('DEDENT'), ])
    
    def test_comments(self):
        self.compare(self._lex("""
            # example
            a: b
            c:
              - d
              # foo
              - e
            """), [ t('INDENT'),
            t('KEY', 'a'), t('INDENT'), t('SCALAR', 'b'), t('DEDENT'),
            t('KEY', 'c'),
            t('INDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'd'), t('DEDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'e'), t('DEDENT'),
            t('DEDENT'),
            t('DEDENT'), ])
        
    
    def test_sample2(self):
        self.compare(self._lex("""
        a:
            b:c
            e:
                - f
                - g
            h:
                i: j"""), [ t('INDENT'),
            t('KEY', 'a'),
            t('INDENT'),
                t('KEY', 'b'), t('INDENT'), t('SCALAR', 'c'), t('DEDENT'),
                t('KEY', 'e'),
                t('INDENT'),
                    t('LISTITEM'), t('INDENT'), t('SCALAR', 'f'), t('DEDENT'),
                    t('LISTITEM'), t('INDENT'), t('SCALAR', 'g'), t('DEDENT'),
                t('DEDENT'),
                t('KEY', 'h'),
                t('INDENT'),
                    t('KEY', 'i'), t('INDENT'), t('SCALAR', 'j'), t('DEDENT'),
                    t('DEDENT'),
                t('DEDENT'),
            t('DEDENT'), ])
    
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
        """), [ t('INDENT'),
            t('KEY', 'key1'), t('INDENT'), t('SCALAR', 'value1'), t('DEDENT'),
            t('KEY', 'key2'), t('INDENT'), t('SCALAR', 'value2'), t('DEDENT'),
            t('KEY', 'key3'),
            t('INDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'item1'), t('DEDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'item2'), t('DEDENT'),
                t('LISTITEM'), t('INDENT'), t('SCALAR', 'item3'), t('DEDENT'),
            t('DEDENT'),
            t('KEY', 'key4'),
            t('INDENT'),
                t('KEY', 'key5'),
                t('INDENT'),
                    t('KEY', 'key6'), t('INDENT'), t('SCALAR', 'key7'), t('DEDENT'),
                t('DEDENT'),
            t('DEDENT'),
            t('DEDENT'), ])

    def test_template(self):
        self.compare(self._lex("foo: {{bar}}"), [
            t('INDENT'),
                t('KEY', 'foo'),
                t('INDENT'), 
                t('LDBRACE'),
                t('IDENTIFIER', 'bar'),
                t('RDBRACE'),
                t('DEDENT'),
            t('DEDENT'),
        ])
        
    def test_multiline(self):
        self.compare(self._lex("""
            foo: |
               bar
               baz
               quux
            bar: |
               x y z
               a b c
        """), [
               t('INDENT'),
                   t('KEY', 'foo'),
                   t('INDENT'), t('SCALAR', "bar\nbaz\nquux\n"), t('DEDENT'),
                   t('KEY', 'bar'),
                   t('INDENT'), t('SCALAR', "x y z\na b c\n"), t('DEDENT'),
                t('DEDENT'),
        ])
        
    def test_deep_multiline_file_end(self):
        self.compare(self._lex("""
            foo:
                bar: |
                    quux
        """), [
               t('INDENT'),
                   t('KEY', 'foo'),
                   t('INDENT'),
                       t('KEY', 'bar'),
                       t('INDENT'), t('SCALAR', 'quux\n'), t('DEDENT'),
                    t('DEDENT'),
                t('DEDENT'),
            ])
        
    def test_multiline_implicit_template(self):
        self.compare(self._lex("""
        foo: |
          bar
          baz
          {{quux}}
        """), [
            t('INDENT'),
                t('KEY', 'foo'),
                t('INDENT'),
                t('SCALAR', 'bar\nbaz\n'),
                t('LDBRACE'),
                t('IDENTIFIER', 'quux'),
                t('RDBRACE'),
                t('SCALAR', '\n'),
                t('DEDENT'),
            t('DEDENT'),
        ])
        
    def test_extend(self):
        self.compare(self._lex("""
        extend foo:
            - baz
            - quux
        """), [
            t('INDENT'),
                t('EXTEND'),
                t('KEY', 'foo'),
                t('INDENT'),
                    t('LISTITEM'), t('INDENT'), t('SCALAR', 'baz'), t('DEDENT'),
                    t('LISTITEM'), t('INDENT'), t('SCALAR', 'quux'), t('DEDENT'),
                t('DEDENT'),
            t('DEDENT'),
            ])
        
    def test_complex_expressions_in_templates(self):
        self.compare(self._lex("""
        foo: this {{a+b+c}} is {{foo("bar")}} hard
        """), [
               t('INDENT'),
               t('KEY', 'foo'),
               t('INDENT'),
               t('SCALAR', 'this '),
               t('LDBRACE'),
               t('IDENTIFIER', 'a'),
               t('+', '+'),
               t('IDENTIFIER', 'b'),
               t('+', '+'),
               t('IDENTIFIER', 'c'),
               t('RDBRACE'),
               t('SCALAR', ' is '),
               t('LDBRACE'),
               t('IDENTIFIER', 'foo'),
               t('(', '('),
               t('LITERAL', 'bar'),
               t(')', ')'),
               t('RDBRACE'),
               t('SCALAR', ' hard'),
               t('DEDENT'),
               t('DEDENT'),
            ])
        
    def test_template_in_listitem(self):
        self.compare(self._lex("""
        foo:
          - a
          - {{bar}}
          - c
        """), [
            t('INDENT'),
                t('KEY', 'foo'),
                t('INDENT'),
                    t('LISTITEM'), t('INDENT'), t('SCALAR', 'a'), t('DEDENT'),
                    t('LISTITEM'), t('INDENT'), 
                        t('LDBRACE'),
                        t('IDENTIFIER', 'bar'), 
                        t('RDBRACE'),
                        t('DEDENT'),
                    t('LISTITEM'), t('INDENT'), t('SCALAR', 'c'), t('DEDENT'),
                t('DEDENT'),
            t('DEDENT'),
        ])

    def test_token(self):
        l = Lexer()
        l.input("""
               a: b
               c: 
                 d: e
            """)
        self.compare([l.token()], [t('INDENT')])
        self.compare([l.token()], [t('KEY', 'a')])
        self.compare([l.token()], [t('INDENT')])
        self.compare([l.token()], [t('SCALAR', 'b')])
        self.compare([l.token()], [t('DEDENT')])
        self.compare([l.token()], [t('KEY', 'c')])
        self.compare([l.token()], [t('INDENT')])
        self.compare([l.token()], [t('KEY', 'd')])
        self.compare([l.token()], [t('INDENT')])
        self.compare([l.token()], [t('SCALAR', 'e')])
        self.compare([l.token()], [t('DEDENT')])
        self.compare([l.token()], [t('DEDENT')])
        self.compare([l.token()], [t('DEDENT')])
    
    def test_include(self):
        self.compare(self._lex("""
        % include "foo.yay"
        """), [
           t('INDENT'), t('%', '%'), t('INCLUDE', 'include'), t('LITERAL', 'foo.yay'), t('DEDENT')])
        