import unittest
from yay.parser import parse

from yay.nodes import *
from yay.ast import *

class TestParser(unittest.TestCase):
    
    def _resolve(self, value):
        result = parse(value).resolve()
        return result
    
    def test_set_integer_literal(self):
        res = parse("% set a = 2")
        self.assertEqual(res, Set('a', Literal(2)))
        
    def test_set_identifier(self):
        res = parse("% set a = b")
        self.assertEqual(res, Set('a', Identifier('b')))
    
    def test_set_addition(self):
        res = parse("% set a = 2+2")
        self.assertEqual(res, Set('a', Expr(Literal(2), Literal(2), '+')))
    
    def test_emptydict(self):
        self.assertEqual(self._resolve("""
        a: {}
        """), {'a': {}})
        
    def test_emptylist(self):
        self.assertEqual(self._resolve("""
        a: []
        """), {'a': []})
    
    def test_simple_dict(self):
        self.assertEqual(self._resolve("""
        a: b
        """), {'a': 'b'})
        
        
    def test_two_item_dict(self):
        self.assertEqual(self._resolve("""
        a: b
        c: d
        """), {'a': 'b', 'c': 'd'})
        
    def test_nested_dict(self):
        self.assertEqual(self._resolve("""
        a:
         b: c
        """), {'a': {'b': 'c'}})
    
    def test_sample1(self):
        self.assertEqual(self._resolve("""
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
        self.assertEqual(self._resolve("""
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
        self.assertEqual(self._resolve("""
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

    def test_list_of_multikey_dicts(self):
        self.assertEqual(self._resolve("""
            a: 
              - b
              - c: d
                e: f
              - g
              """), {
                'a': [
                'b',
                {'c': 'd', 'e': 'f'},
                'g',
                ]})

    def test_list_of_dicts_with_lists_in(self):
        self.assertEqual(self._resolve("""
            a:
             - b: c
               d:
                 - e
                 - f
                 - g
              """), {'a': [{'b': 'c', 'd': ['e', 'f', 'g']}]})

    def test_simple_overlay(self):
        self.assertEqual(self._resolve("""
        foo: 
          a: b
          
        foo:
          c: d
        """), {
               'foo': {
                   'a': 'b',
                   'c': 'd',
                   }
               })
        
