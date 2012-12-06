
import unittest
from yay.lexer import Lexer
from ply.lex import LexToken

def tok(name, value=None):
    t = LexToken()
    t.type = name
    t.value = value
    t.lineno = 0
    t.lexpos = 0
    return t

class TestLexer(unittest.TestCase):
    
    def _lex(self, value):
        l = Lexer()
        l.input(value)
        l.done()
        return list(l)
    
    def compare(self, x, y):
        """ Compare two lists of LexTokens """
        if len(x) != len(y):
            raise self.failureException("Token lists are of different lengths")
        for a, b in zip(x,y):
            if a.value != b.value or a.type != b.type:
                raise self.failureException("Tokens %r %r differ" % (a,b))
    
    def test_list_of_multikey_dicts(self):
        result = self._lex("""
            a: 
              - b
              - c: d
                e: f
              - g
              """)
        self.compare(result, [ tok('BLOCK'),
            tok('KEY', 'a'),
            tok('BLOCK'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'b'), tok('END'),
                tok('LISTITEM'),
                tok('BLOCK'),
                    tok('KEY', 'c'), tok('BLOCK'), tok('SCALAR', 'd'), tok('END'),
                    tok('KEY', 'e'), tok('BLOCK'), tok('SCALAR', 'f'), tok('END'),
                tok('END'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'g'), tok('END'),
            tok('END'),
            tok('END'), ])

    def test_list_of_dicts(self):
        self.compare(self._lex("""
            a:
              - b
              - c: d
              - e
        """), [ tok('BLOCK'),
            tok('KEY', 'a'),
            tok('BLOCK'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'b'), tok('END'),
                tok('LISTITEM'),
                tok('BLOCK'),
                    tok('KEY', 'c'), tok('BLOCK'), tok('SCALAR', 'd'), tok('END'),
                tok('END'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'e'), tok('END'),
            tok('END'),
        tok('END'), ])
    
    def test_initial1(self):
        self.compare(self._lex("""
               a: b
               c: 
                 d: e
            """), [ tok('BLOCK'),
            tok('KEY', 'a'), tok('BLOCK'), tok('SCALAR', 'b'), tok('END'),
            tok('KEY', 'c'),
            tok('BLOCK'),
                tok('KEY', 'd'), tok('BLOCK'), tok('SCALAR', 'e'), tok('END'),
            tok('END'),
            tok('END'), ])
    
    def test_emptydict(self):
        self.compare(self._lex("a: {}"), [ tok('BLOCK'),
            tok('KEY', 'a'), tok('BLOCK'), tok('EMPTYDICT', ), tok('END'),
            tok('END'), ])
        
    def test_emptylist(self):
        self.compare(self._lex("a: []"), [ tok('BLOCK'),
            tok('KEY', 'a'), tok('BLOCK'), tok('EMPTYLIST'), tok('END'),
            tok('END'), ])
    
    def test_comments(self):
        self.compare(self._lex("""
            # example
            a: b
            c:
              - d
              # foo
              - e
            """), [ tok('BLOCK'),
            tok('KEY', 'a'), tok('BLOCK'), tok('SCALAR', 'b'), tok('END'),
            tok('KEY', 'c'),
            tok('BLOCK'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'd'), tok('END'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'e'), tok('END'),
            tok('END'),
            tok('END'), ])
        
    
    def test_sample2(self):
        self.compare(self._lex("""
        a:
            b:c
            e:
                - f
                - g
            h:
                i: j"""), [ tok('BLOCK'),
            tok('KEY', 'a'),
            tok('BLOCK'),
                tok('KEY', 'b'), tok('BLOCK'), tok('SCALAR', 'c'), tok('END'),
                tok('KEY', 'e'),
                tok('BLOCK'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'f'), tok('END'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'g'), tok('END'),
                tok('END'),
                tok('KEY', 'h'),
                tok('BLOCK'),
                    tok('KEY', 'i'), tok('BLOCK'), tok('SCALAR', 'j'), tok('END'),
                    tok('END'),
                tok('END'),
            tok('END'), ])
    
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
        """), [ tok('BLOCK'),
            tok('KEY', 'key1'), tok('BLOCK'), tok('SCALAR', 'value1'), tok('END'),
            tok('KEY', 'key2'), tok('BLOCK'), tok('SCALAR', 'value2'), tok('END'),
            tok('KEY', 'key3'),
            tok('BLOCK'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'item1'), tok('END'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'item2'), tok('END'),
                tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'item3'), tok('END'),
            tok('END'),
            tok('KEY', 'key4'),
            tok('BLOCK'),
                tok('KEY', 'key5'),
                tok('BLOCK'),
                    tok('KEY', 'key6'), tok('BLOCK'), tok('SCALAR', 'key7'), tok('END'),
                tok('END'),
            tok('END'),
            tok('END'), ])

    def test_explicit_j2(self):
        self.compare(self._lex("""
        foo j2:
            % for p in q:
                - x: {{p}}
            % endfor
        """), [
            tok('BLOCK'),
                tok('KEY', 'foo'),
                tok('BLOCK'),
                    tok('TEMPLATE', ('j2', "% for p in q:\n    - x: {{p}}\n% endfor\n")),
                tok('END'),
            tok('END'),
        ])
            
    def test_implicit_j2(self):
        self.compare(self._lex("foo: {{bar}}"), [
            tok('BLOCK'),
                tok('KEY', 'foo'),
                tok('BLOCK'), tok('TEMPLATE', ('j2', '{{bar}}')), tok('END'),
            tok('END'),
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
               tok('BLOCK'),
                   tok('KEY', 'foo'),
                   tok('BLOCK'), tok('SCALAR', "bar\nbaz\nquux\n"), tok('END'),
                   tok('KEY', 'bar'),
                   tok('BLOCK'), tok('SCALAR', "x y z\na b c\n"), tok('END'),
                tok('END'),
        ])
        
    def test_deep_multiline_file_end(self):
        self.compare(self._lex("""
            foo:
                bar: |
                    quux
        """), [
               tok('BLOCK'),
                   tok('KEY', 'foo'),
                   tok('BLOCK'),
                       tok('KEY', 'bar'),
                       tok('BLOCK'), tok('SCALAR', 'quux\n'), tok('END'),
                    tok('END'),
                tok('END'),
            ])
        
    def test_multiline_implicit_j2(self):
        self.compare(self._lex("""
        foo: |
          bar
          baz
          {{quux}}
        """), [
            tok('BLOCK'),
                tok('KEY', 'foo'),
                tok('BLOCK'), tok('TEMPLATE', ('j2', 'bar\nbaz\n{{quux}}\n')), tok('END'),
            tok('END'),
        ])
        
    def test_extend(self):
        self.compare(self._lex("""
        foo extend:
            - baz
            - quux
        """), [
            tok('BLOCK'),
                tok('KEY', 'foo'),
                tok('EXTEND'),
                tok('BLOCK'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'baz'), tok('END'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'quux'), tok('END'),
                tok('END'),
            tok('END'),
            ])
        
    def test_extend_j2(self):
        self.compare(self._lex("""
        foo extend j2:
            - baz
            - quux
        """), [
            tok('BLOCK'),
                tok('KEY', 'foo'),
                tok('EXTEND'),
                tok('BLOCK'), tok('TEMPLATE', ('j2', '- baz\n- quux\n')), tok('END'),
            tok('END'),
        ])
        
    def test_j2_listitem(self):
        self.compare(self._lex("""
        foo:
          - a
          - {{bar}}
          - c
        """), [
            tok('BLOCK'),
                tok('KEY', 'foo'),
                tok('BLOCK'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'a'), tok('END'),
                    tok('LISTITEM'), tok('BLOCK'), tok('TEMPLATE', ('j2', '{{bar}}')), tok('END'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'c'), tok('END'),
                tok('END'),
            tok('END'),
        ])

    def test_include(self):
        self.compare(self._lex("""
        yay include:
            - foo.yay
            - bar.yay
        """), [
            tok('BLOCK'),
                tok('DIRECTIVE', 'include'),
                tok('BLOCK'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'foo.yay'), tok('END'),
                    tok('LISTITEM'), tok('BLOCK'), tok('SCALAR', 'bar.yay'), tok('END'),
                tok('END'),
            tok('END'),
        ])
        
    def test_madness(self):
        self.compare(self._lex("""
        yay search:
            - {{foo}}
        """), [
            tok('BLOCK'),
                tok('DIRECTIVE', 'search'),
                tok('BLOCK'),
                    tok('LISTITEM'), tok('BLOCK'), tok('TEMPLATE', ('j2', '{{foo}}')), tok('END'),
                tok('END'),
            tok('END'),
        ])
        
    def test_more_madness(self):
        self.compare(self._lex("""
        yay search j2:
            - {{foo}}
        """), [
            tok('BLOCK'),
                tok('DIRECTIVE', 'search'),
                tok('BLOCK'),
                tok('TEMPLATE', ('j2', '- {{foo}}\n')),
                tok('END'),
            tok('END'),
        ])

    def test_token(self):
        l = Lexer()
        l.input("""
               a: b
               c: 
                 d: e
            """)
        self.compare([l.token()], [tok('BLOCK')])
        self.compare([l.token()], [tok('KEY', 'a')])
        self.compare([l.token()], [tok('BLOCK')])
        self.compare([l.token()], [tok('SCALAR', 'b')])
        self.compare([l.token()], [tok('END')])
        self.compare([l.token()], [tok('KEY', 'c')])
        self.compare([l.token()], [tok('BLOCK')])
        self.compare([l.token()], [tok('KEY', 'd')])
        self.compare([l.token()], [tok('BLOCK')])
        self.compare([l.token()], [tok('SCALAR', 'e')])
        self.compare([l.token()], [tok('END')])
        self.compare([l.token()], [tok('END')])
        self.compare([l.token()], [tok('END')])
    