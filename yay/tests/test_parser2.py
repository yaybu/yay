import unittest
from yay import parser2

class TestParser(unittest.TestCase):
    
    def _parse(self, value):
        parser = parser2.Parser()
        parser.input(value)
        d = parser.parse()
        return d
    
    def test_sample1(self):
        self.assertEqual(self._parse("""
        key1: value1
        
        key2: value2
        
        key3: 
          - item1
          - item2
          - item3
          
        key4:
            key5:
                key6: key7
        """), {
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
        self.assertEqual(self._parse("""
        key1:
            key2:
                - a
                - b
            key3: c
            key4:
                key5: d
        """), {
            'key1': {
                'key2': ['a', 'b'],
                'key3': 'c',
                'key4': {
                    'key5': 'd'
                    }
                }
            })
    
    def test_list_of_dicts(self):
        self.assertEqual(self._parse("""
            a: 
              - b
              - c: d
              - e
              """), {
                'a': [
                'b',
                {'c': 'd'},
                'e',
                ]})