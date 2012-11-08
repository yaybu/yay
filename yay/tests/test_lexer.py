
import unittest
from yay.lexer import Lexer, END, KEY, SCALAR, LISTITEM, EMPTYDICT, EMPTYLIST

class TestLexer(unittest.TestCase):
    
    def _lex(self, value):
        l = Lexer()
        l.input(value)
        l.done()
        return list(l.tokens())
    
    def test_list_of_multikey_dicts(self):
        self.assertEqual(self._lex("""
            a: 
              - b
              - c: d
                e: f
              - g
              """), [
            KEY('a'),
                LISTITEM('b'),
                KEY('c'), SCALAR('d'), END(),
                KEY('e'), SCALAR('f'), END(),
                END(),
                LISTITEM('g'),
                END(),
            ])

    def test_list_of_dicts(self):
        self.assertEqual(self._lex("""
            a:
              - b
              - c: d
              - e
        """), [
            KEY('a'),
                LISTITEM('b'),
                KEY('c'), SCALAR('d'), END(),
                END(),
                LISTITEM('e'),
                END(),
        ])
    
    def test_initial1(self):
        self.assertEqual(self._lex("""
               a: b
               c: 
                 d: e
            """), [
            KEY('a'), SCALAR('b'), END(),
            KEY('c'),
                KEY('d'), SCALAR('e'), END(),
                END(),
            ])
    
    def test_emptydict(self):
        self.assertEqual(self._lex("a: {}"), [
            KEY('a'), EMPTYDICT(), END()
            ])
        
    def test_emptylist(self):
        self.assertEqual(self._lex("a: []"), [
            KEY('a'), EMPTYLIST(), END()
            ])
    
    def test_comments(self):
        self.assertEqual(self._lex("""
            # example
            a: b
            c:
              - d
              # foo
              - e
            """), [
            KEY('a'), SCALAR('b'), END(),
            KEY('c'),
                LISTITEM('d'),
                LISTITEM('e'),
                END(),
            ])
        
    
    def test_sample2(self):
        self.assertEqual(self._lex("""
        a:
            b:c
            e:
                - f
                - g
            h:
                i: j"""), [
            KEY('a'),
                KEY('b'), SCALAR('c'), END(),
                KEY('e'),
                    LISTITEM('f'),
                    LISTITEM('g'),
                    END(),
                KEY('h'),
                    KEY('i'), SCALAR('j'), END(),
                    END(),
                END(),
            ])
            
        
    
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
        """), [
            KEY('key1'), SCALAR('value1'), END(),
            KEY('key2'), SCALAR('value2'), END(),
            KEY('key3'),
                LISTITEM('item1'),
                LISTITEM('item2'),
                LISTITEM('item3'),
                END(),
            KEY('key4'),
                KEY('key5'),
                    KEY('key6'), SCALAR('key7'), END(),
                    END(),
                END(),
            ])

