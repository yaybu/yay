
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
        self.compare(p("'foo'"), [t('LITERAL', "'foo'")])
        self.compare(p("('foo')"), ['(', t('LITERAL', "'foo'"), ')'])
        self.compare(p("a + 'foo'"), [t('IDENTIFIER', 'a'), '+', t('LITERAL', "'foo'")])
        self.compare(p("a+2"), [t('IDENTIFIER', 'a'), '+', t('LITERAL', 2)])
        self.compare(p("a<<5"), [t('IDENTIFIER', 'a'), t('LSHIFT', "<<"), t('LITERAL', 5)])
        self.compare(p("a<5"), [t('IDENTIFIER', 'a'), '<', t('LITERAL', 5)])
        self.compare(p("a and 5"), [t('IDENTIFIER', 'a'), t('AND', 'and'), t('LITERAL', 5)])
        self.compare(p("a andy 5"), [t('IDENTIFIER', 'a'), t('IDENTIFIER', 'andy'), t('LITERAL', 5)])
        self.compare(p("[1,2.0,'foo']"), ['[', t('LITERAL', 1), ',', t('LITERAL', 2.0), ',', t('LITERAL', "'foo'"), ']'])
    
    def compare(self, x, y):
        """ Compare two lists of ts """
        if type(x) == types.GeneratorType:
            x = list(x)
        if len(x) != len(y):
            raise self.failureException("Token lists are of different lengths: %r %r", (x, y))
        for a, b in zip(x,y):
            if type(a) != type(b):
                raise self.failureException("Tokens %r %r differ" % (a,b))                
            elif type(a) in types.StringTypes:
                if a != b:
                    raise self.failureException("Tokens %r %r differ" % (a,b))                                    
            elif a.value != b.value or a.type != b.type:
                raise self.failureException("Tokens %r %r differ" % (a,b))
    
    def test_list_of_multikey_dicts(self):
        result = self._lex("""
            a: 
              - b
              - c: d
                e: f
              - g
              """)
        self.compare(result, [ t('BLOCK'),
            t('KEY', 'a'),
            t('BLOCK'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'b'), t('END'),
                t('LISTITEM'),
                t('BLOCK'),
                    t('KEY', 'c'), t('BLOCK'), t('SCALAR', 'd'), t('END'),
                    t('KEY', 'e'), t('BLOCK'), t('SCALAR', 'f'), t('END'),
                t('END'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'g'), t('END'),
            t('END'),
            t('END'), ])

    def test_list_of_dicts(self):
        self.compare(self._lex("""
            a:
              - b
              - c: d
              - e
        """), [ t('BLOCK'),
            t('KEY', 'a'),
            t('BLOCK'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'b'), t('END'),
                t('LISTITEM'),
                t('BLOCK'),
                    t('KEY', 'c'), t('BLOCK'), t('SCALAR', 'd'), t('END'),
                t('END'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'e'), t('END'),
            t('END'),
        t('END'), ])
    
    def test_initial1(self):
        self.compare(self._lex("""
               a: b
               c: 
                 d: e
            """), [ t('BLOCK'),
            t('KEY', 'a'), t('BLOCK'), t('SCALAR', 'b'), t('END'),
            t('KEY', 'c'),
            t('BLOCK'),
                t('KEY', 'd'), t('BLOCK'), t('SCALAR', 'e'), t('END'),
            t('END'),
            t('END'), ])
    
    def test_emptydict(self):
        self.compare(self._lex("a: {}"), [ t('BLOCK'),
            t('KEY', 'a'), t('BLOCK'), t('EMPTYDICT', ), t('END'),
            t('END'), ])
        
    def test_emptylist(self):
        self.compare(self._lex("a: []"), [ t('BLOCK'),
            t('KEY', 'a'), t('BLOCK'), t('EMPTYLIST'), t('END'),
            t('END'), ])
    
    def test_comments(self):
        self.compare(self._lex("""
            # example
            a: b
            c:
              - d
              # foo
              - e
            """), [ t('BLOCK'),
            t('KEY', 'a'), t('BLOCK'), t('SCALAR', 'b'), t('END'),
            t('KEY', 'c'),
            t('BLOCK'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'd'), t('END'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'e'), t('END'),
            t('END'),
            t('END'), ])
        
    
    def test_sample2(self):
        self.compare(self._lex("""
        a:
            b:c
            e:
                - f
                - g
            h:
                i: j"""), [ t('BLOCK'),
            t('KEY', 'a'),
            t('BLOCK'),
                t('KEY', 'b'), t('BLOCK'), t('SCALAR', 'c'), t('END'),
                t('KEY', 'e'),
                t('BLOCK'),
                    t('LISTITEM'), t('BLOCK'), t('SCALAR', 'f'), t('END'),
                    t('LISTITEM'), t('BLOCK'), t('SCALAR', 'g'), t('END'),
                t('END'),
                t('KEY', 'h'),
                t('BLOCK'),
                    t('KEY', 'i'), t('BLOCK'), t('SCALAR', 'j'), t('END'),
                    t('END'),
                t('END'),
            t('END'), ])
    
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
        """), [ t('BLOCK'),
            t('KEY', 'key1'), t('BLOCK'), t('SCALAR', 'value1'), t('END'),
            t('KEY', 'key2'), t('BLOCK'), t('SCALAR', 'value2'), t('END'),
            t('KEY', 'key3'),
            t('BLOCK'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'item1'), t('END'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'item2'), t('END'),
                t('LISTITEM'), t('BLOCK'), t('SCALAR', 'item3'), t('END'),
            t('END'),
            t('KEY', 'key4'),
            t('BLOCK'),
                t('KEY', 'key5'),
                t('BLOCK'),
                    t('KEY', 'key6'), t('BLOCK'), t('SCALAR', 'key7'), t('END'),
                t('END'),
            t('END'),
            t('END'), ])

    def test_template(self):
        self.compare(self._lex("foo: {{bar}}"), [
            t('BLOCK'),
                t('KEY', 'foo'),
                t('BLOCK'), 
                t('LDBRACE'),
                t('VAR', 'bar'),
                t('RDBRACE'),
                t('END'),
            t('END'),
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
               t('BLOCK'),
                   t('KEY', 'foo'),
                   t('BLOCK'), t('SCALAR', "bar\nbaz\nquux\n"), t('END'),
                   t('KEY', 'bar'),
                   t('BLOCK'), t('SCALAR', "x y z\na b c\n"), t('END'),
                t('END'),
        ])
        
    def test_deep_multiline_file_end(self):
        self.compare(self._lex("""
            foo:
                bar: |
                    quux
        """), [
               t('BLOCK'),
                   t('KEY', 'foo'),
                   t('BLOCK'),
                       t('KEY', 'bar'),
                       t('BLOCK'), t('SCALAR', 'quux\n'), t('END'),
                    t('END'),
                t('END'),
            ])
        
    def test_multiline_implicit_template(self):
        self.compare(self._lex("""
        foo: |
          bar
          baz
          {{quux}}
        """), [
            t('BLOCK'),
                t('KEY', 'foo'),
                t('BLOCK'),
                t('SCALAR', 'bar\nbaz\n'),
                t('LDBRACE'),
                t('VAR', 'quux'),
                t('RDBRACE'),
                t('SCALAR', '\n'),
                t('END'),
            t('END'),
        ])
        
    def test_extend(self):
        self.compare(self._lex("""
        extend foo:
            - baz
            - quux
        """), [
            t('BLOCK'),
                t('EXTEND'),
                t('KEY', 'foo'),
                t('BLOCK'),
                    t('LISTITEM'), t('BLOCK'), t('SCALAR', 'baz'), t('END'),
                    t('LISTITEM'), t('BLOCK'), t('SCALAR', 'quux'), t('END'),
                t('END'),
            t('END'),
            ])
        
    def test_complex_expressions_in_templates(self):
        self.compare(self._lex("""
        foo: this {{a+b+c}} is {{foo("bar")}} hard
        """), [
               t('BLOCK'),
               t('KEY', 'foo'),
               t('BLOCK'),
               t('SCALAR', 'this '),
               t('LDBRACE'),
               t('VAR', 'a'),
               t('OP', '+'),
               t('VAR', 'b'),
               t('OP', '+'),
               t('VAR', 'c'),
               t('RDBRACE'),
               t('SCALAR', ' is '),
               t('LDBRACE'),
               t('VAR', 'foo'),
               t('LPAREN', '('),
               t('STRING', '"bar"'),
               t('RPAREN', ')'),
               t('RDBRACE'),
               t('SCALAR', ' hard'),
               t('END'),
               t('END'),
            ])
        
    def test_template_in_listitem(self):
        self.compare(self._lex("""
        foo:
          - a
          - {{bar}}
          - c
        """), [
            t('BLOCK'),
                t('KEY', 'foo'),
                t('BLOCK'),
                    t('LISTITEM'), t('BLOCK'), t('SCALAR', 'a'), t('END'),
                    t('LISTITEM'), t('BLOCK'), 
                        t('LDBRACE'),
                        t('VAR', 'bar'), 
                        t('RDBRACE'),
                        t('END'),
                    t('LISTITEM'), t('BLOCK'), t('SCALAR', 'c'), t('END'),
                t('END'),
            t('END'),
        ])

    def test_token(self):
        l = Lexer()
        l.input("""
               a: b
               c: 
                 d: e
            """)
        self.compare([l.token()], [t('BLOCK')])
        self.compare([l.token()], [t('KEY', 'a')])
        self.compare([l.token()], [t('BLOCK')])
        self.compare([l.token()], [t('SCALAR', 'b')])
        self.compare([l.token()], [t('END')])
        self.compare([l.token()], [t('KEY', 'c')])
        self.compare([l.token()], [t('BLOCK')])
        self.compare([l.token()], [t('KEY', 'd')])
        self.compare([l.token()], [t('BLOCK')])
        self.compare([l.token()], [t('SCALAR', 'e')])
        self.compare([l.token()], [t('END')])
        self.compare([l.token()], [t('END')])
        self.compare([l.token()], [t('END')])
    
    def test_include(self):
        self.compare(self._lex("""
        % include "foo.yay"
        """), [])
        