
import unittest
from yay.lexer import (Lexer, BLOCK, END, KEY, SCALAR,
                       LISTITEM, EMPTYDICT, EMPTYLIST,
                       TEMPLATE, EXTEND, DIRECTIVE)

class TestLexer(unittest.TestCase):
    
    def _lex(self, value):
        l = Lexer()
        l.input(value)
        l.done()
        return list(l.tokens())
    
    def test_list_of_multikey_dicts(self):
        result = self._lex("""
            a: 
              - b
              - c: d
                e: f
              - g
              """)
        self.assertEqual(result, [ BLOCK(),
            KEY('a'),
            BLOCK(),
                LISTITEM(), BLOCK(), SCALAR('b'), END(),
                LISTITEM(),
                BLOCK(),
                    KEY('c'), BLOCK(), SCALAR('d'), END(),
                    KEY('e'), BLOCK(), SCALAR('f'), END(),
                END(),
                LISTITEM(), BLOCK(), SCALAR('g'), END(),
            END(),
            END(), ])

    def test_list_of_dicts(self):
        self.assertEqual(self._lex("""
            a:
              - b
              - c: d
              - e
        """), [ BLOCK(),
            KEY('a'),
            BLOCK(),
                LISTITEM(), BLOCK(), SCALAR('b'), END(),
                LISTITEM(),
                BLOCK(),
                    KEY('c'), BLOCK(), SCALAR('d'), END(),
                END(),
                LISTITEM(), BLOCK(), SCALAR('e'), END(),
            END(),
        END(), ])
    
    def test_initial1(self):
        self.assertEqual(self._lex("""
               a: b
               c: 
                 d: e
            """), [ BLOCK(),
            KEY('a'), BLOCK(), SCALAR('b'), END(),
            KEY('c'),
            BLOCK(),
                KEY('d'), BLOCK(), SCALAR('e'), END(),
            END(),
            END(), ])
    
    def test_emptydict(self):
        self.assertEqual(self._lex("a: {}"), [ BLOCK(),
            KEY('a'), BLOCK(), EMPTYDICT(), END(),
            END(), ])
        
    def test_emptylist(self):
        self.assertEqual(self._lex("a: []"), [ BLOCK(),
            KEY('a'), BLOCK(), EMPTYLIST(), END(),
            END(), ])
    
    def test_comments(self):
        self.assertEqual(self._lex("""
            # example
            a: b
            c:
              - d
              # foo
              - e
            """), [ BLOCK(),
            KEY('a'), BLOCK(), SCALAR('b'), END(),
            KEY('c'),
            BLOCK(),
                LISTITEM(), BLOCK(), SCALAR('d'), END(),
                LISTITEM(), BLOCK(), SCALAR('e'), END(),
            END(),
            END(), ])
        
    
    def test_sample2(self):
        self.assertEqual(self._lex("""
        a:
            b:c
            e:
                - f
                - g
            h:
                i: j"""), [ BLOCK(),
            KEY('a'),
            BLOCK(),
                KEY('b'), BLOCK(), SCALAR('c'), END(),
                KEY('e'),
                BLOCK(),
                    LISTITEM(), BLOCK(), SCALAR('f'), END(),
                    LISTITEM(), BLOCK(), SCALAR('g'), END(),
                END(),
                KEY('h'),
                BLOCK(),
                    KEY('i'), BLOCK(), SCALAR('j'), END(),
                    END(),
                END(),
            END(), ])
    
    def test_sample1(self):
        self.assertEqual(self._lex("""
            key1: value1
            
            key2: value2
            
            key3: 
              - item1
              - item2
              - item3
              
            key4:
                key5:
                    key6: key7
        """), [ BLOCK(),
            KEY('key1'), BLOCK(), SCALAR('value1'), END(),
            KEY('key2'), BLOCK(), SCALAR('value2'), END(),
            KEY('key3'),
            BLOCK(),
                LISTITEM(), BLOCK(), SCALAR('item1'), END(),
                LISTITEM(), BLOCK(), SCALAR('item2'), END(),
                LISTITEM(), BLOCK(), SCALAR('item3'), END(),
            END(),
            KEY('key4'),
            BLOCK(),
                KEY('key5'),
                BLOCK(),
                    KEY('key6'), BLOCK(), SCALAR('key7'), END(),
                END(),
            END(),
            END(), ])

    def test_explicit_j2(self):
        self.assertEqual(self._lex("""
        foo j2:
            % for p in q:
                - x: {{p}}
            % endfor
        """), [
            BLOCK(),
                KEY('foo'),
                BLOCK(),
                    TEMPLATE(('j2', "% for p in q:\n    - x: {{p}}\n% endfor\n")),
                END(),
            END(),
        ])
            
    def test_implicit_j2(self):
        self.assertEqual(self._lex("foo: {{bar}}"), [
            BLOCK(),
                KEY('foo'),
                BLOCK(), TEMPLATE(('j2', '{{bar}}')), END(),
            END(),
        ])
        
    def test_multiline(self):
        self.assertEqual(self._lex("""
            foo: |
               bar
               baz
               quux
            bar: |
               x y z
               a b c
        """), [
               BLOCK(),
                   KEY('foo'),
                   BLOCK(), SCALAR("bar\nbaz\nquux\n"), END(),
                   KEY('bar'),
                   BLOCK(), SCALAR("x y z\na b c\n"), END(),
                END(),
        ])
        
    def test_deep_multiline_file_end(self):
        self.assertEqual(self._lex("""
            foo:
                bar: |
                    quux
        """), [
               BLOCK(),
                   KEY('foo'),
                   BLOCK(),
                       KEY('bar'),
                       BLOCK(), SCALAR('quux\n'), END(),
                    END(),
                END(),
            ])
        
    def test_multiline_implicit_j2(self):
        self.assertEqual(self._lex("""
        foo: |
          bar
          baz
          {{quux}}
        """), [
            BLOCK(),
                KEY('foo'),
                BLOCK(), TEMPLATE(('j2', 'bar\nbaz\n{{quux}}\n')), END(),
            END(),
        ])
        
    def test_extend(self):
        self.assertEqual(self._lex("""
        foo extend:
            - baz
            - quux
        """), [
            BLOCK(),
                KEY('foo'),
                EXTEND(),
                BLOCK(),
                    LISTITEM(), BLOCK(), SCALAR('baz'), END(),
                    LISTITEM(), BLOCK(), SCALAR('quux'), END(),
                END(),
            END(),
            ])
        
    def test_extend_j2(self):
        self.assertEqual(self._lex("""
        foo extend j2:
            - baz
            - quux
        """), [
            BLOCK(),
                KEY('foo'),
                EXTEND(),
                BLOCK(), TEMPLATE(('j2', '- baz\n- quux\n')), END(),
            END(),
        ])
        
    def test_j2_listitem(self):
        self.assertEqual(self._lex("""
        foo:
          - a
          - {{bar}}
          - c
        """), [
            BLOCK(),
                KEY('foo'),
                BLOCK(),
                    LISTITEM(), BLOCK(), SCALAR('a'), END(),
                    LISTITEM(), BLOCK(), TEMPLATE(('j2', '{{bar}}')), END(),
                    LISTITEM(), BLOCK(), SCALAR('c'), END(),
                END(),
            END(),
        ])

    def test_include(self):
        self.assertEqual(self._lex("""
        yay include:
            - foo.yay
            - bar.yay
        """), [
            BLOCK(),
                DIRECTIVE('include'),
                BLOCK(),
                    LISTITEM(), BLOCK(), SCALAR('foo.yay'), END(),
                    LISTITEM(), BLOCK(), SCALAR('bar.yay'), END(),
                END(),
            END(),
        ])
        
    def test_madness(self):
        self.assertEqual(self._lex("""
        yay search:
            - {{foo}}
        """), [
            BLOCK(),
                DIRECTIVE('search'),
                BLOCK(),
                    LISTITEM(), BLOCK(), TEMPLATE(('j2', '{{foo}}')), END(),
                END(),
            END(),
        ])
        
    def test_more_madness(self):
        self.assertEqual(self._lex("""
        yay search j2:
            - {{foo}}
        """), [
            BLOCK(),
                DIRECTIVE('search'),
                BLOCK(),
                TEMPLATE(('j2', '- {{foo}}\n')),
                END(),
            END(),
        ])
