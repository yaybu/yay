
import unittest
from yay.lexer import Lexer, BLOCK, ENDBLOCK, KEY, VALUE, LISTVALUE

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

        


class TestLexer(unittest.TestCase):
    
    def test_sample1(self):
        l = Lexer()
        l.input(sample1)
        l.done()
        self.assertEqual(list(l.tokens()), [
                              KEY('key1'),
                              BLOCK(),
                              VALUE('value1'),
                              ENDBLOCK(),
                              KEY('key2'),
                              BLOCK(),
                              VALUE('value2'),
                              ENDBLOCK(),
                              KEY('key3'),
                              BLOCK(),
                              LISTVALUE('item1'),
                              LISTVALUE('item2'),
                              LISTVALUE('item3'),
                              ENDBLOCK(),
                              KEY('key4'),
                              BLOCK(),
                              KEY('key5'),
                              BLOCK(),
                              KEY('key6'),
                              BLOCK(),
                              VALUE('key7'),
                              ENDBLOCK(),
                              ENDBLOCK(),
                              ENDBLOCK(),
                              ])
            