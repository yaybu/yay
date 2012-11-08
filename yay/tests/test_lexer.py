
import unittest
from yay.lexer import Lexer, BLOCK, END, KEY, SCALAR, LISTITEM, EMPTYDICT, EMPTYLIST

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

