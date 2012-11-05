
import unittest
from yay.lexer import Lexer, ENDBLOCK, KEY, VALUE, LISTVALUE, EMPTYDICT, EMPTYLIST

sample1 = """
key1: value1

key2: value2

key3: 
  - item1
  - item2
  - item3
  
key4:
    key5:
        key6: key7
"""

sample2 = """
a:
    b:c
    e:
        - f
        - g
    h:
        i: j
"""

comments = """

# example
a: b
c:
  - d
  # foo
  - e
 
"""

emptylist = """
a: []
"""

emptydict = """
a: {}
"""

class TestLexer(unittest.TestCase):
    
    def _lex(self, value):
        l = Lexer()
        l.input(value)
        l.done()
        return list(l.tokens())
    
    def test_emptydict(self):
        self.assertEqual(self._lex(emptydict), [
            KEY('a'),
            EMPTYDICT(),
            ENDBLOCK()
            ])
        
    def test_emptylist(self):
        self.assertEqual(self._lex(emptylist), [
            KEY('a'),
            EMPTYLIST(),
            ENDBLOCK()
            ])
    
    def test_comments(self):
        self.assertEqual(self._lex(comments), [
            KEY('a'),
            VALUE('b'),
            ENDBLOCK(),
            KEY('c'),
            LISTVALUE('d'),
            LISTVALUE('e'),
            ENDBLOCK(),
            ])
        
    
    def test_sample2(self):
        l = Lexer()
        l.input(sample2)
        l.done()
        self.assertEqual(list(l.tokens()), [
            KEY('a'),
            KEY('b'),
            VALUE('c'),
            ENDBLOCK(),
            KEY('e'),
            LISTVALUE('f'),
            LISTVALUE('g'),
            ENDBLOCK(),
            KEY('h'),
            KEY('i'),
            VALUE('j'),
            ENDBLOCK(),
            ENDBLOCK(),
            ENDBLOCK(),
            ])
            
        
    
    def test_sample1(self):
        l = Lexer()
        l.input(sample1)
        l.done()
        self.assertEqual(list(l.tokens()), [
                              KEY('key1'),
                              VALUE('value1'),
                              ENDBLOCK(),
                              KEY('key2'),
                              VALUE('value2'),
                              ENDBLOCK(),
                              KEY('key3'),
                              LISTVALUE('item1'),
                              LISTVALUE('item2'),
                              LISTVALUE('item3'),
                              ENDBLOCK(),
                              KEY('key4'),
                              KEY('key5'),
                              KEY('key6'),
                              VALUE('key7'),
                              ENDBLOCK(),
                              ENDBLOCK(),
                              ENDBLOCK(),
                              ])
            