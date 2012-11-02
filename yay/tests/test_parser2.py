import unittest
from yay import parser2

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
key1:
    key2:
        - a
        - b
    key3: c
    key4:
        key5: d
"""
    
class TestParser(unittest.TestCase):
    
    def test_sample1(self):
        parser = parser2.Parser()
        parser.input(sample1)
        d = parser.parse()
        self.assertEqual(d, {
            'key1': 'value1',
            'key2': 'value2',
            'key3': ['item1', 'item2', 'item3'],
            'key4': {
                'key5': {
                    'key6': 'key7'
                    }
                }
            })

    def test_sample2(self):
        parser = parser2.Parser()
        parser.input(sample2)
        d = parser.parse()
        self.assertEqual(d, {
            'key1': {
                'key2': ['a', 'b'],
                'key3': 'c',
                'key4': {
                    'key5': 'd'
                    }
                }
            })