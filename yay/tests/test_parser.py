import unittest
from yay import parser
from yay.nodes import *
from yay.ast import *

def parse(value):
    return parser.parse(value, debug=0) 

class TestParser(unittest.TestCase):
    
    def _resolve(self, value):
        result = parse(value).resolve()
        return result
    
    def test_set_integer_literal(self):
        res = parse("% set a = 2")
        self.assertEqual(res, Set('a', Literal(2)))
        
    def test_set_string_literal(self):
        res = parse("% set a = 'foo'")
        self.assertEqual(res, Set('a', Literal("foo")))
                
    def test_set_float_literal(self):
        res = parse("% set a = 2.4")
        self.assertEqual(res, Set('a', Literal(2.4)))
        
    def test_set_identifier(self):
        res = parse("% set a = b")
        self.assertEqual(res, Set('a', Identifier('b')))
    
    def test_set_addition(self):
        res = parse("% set a = 2+2")
        self.assertEqual(res, Set('a', Expr(Literal(2), Literal(2), '+')))
        
    def test_set_complex_expr(self):
        res = parse("% set a = (2+2)*5/12.0")
        self.assertEqual(res, Set('a', 
            Expr(
                Expr(
                    ParentForm(
                        ExpressionList(
                            Expr(Literal(2), Literal(2), '+'),
                            )
                        ),
                    Literal(5),
                    '*'),
                Literal(12.0),
                '/')
            ))
        
    def test_set_list(self):
        res = parse("% set a = [1,2,3,4]")
        self.assertEqual(res, Set('a', ListDisplay(ExpressionList(*map(Literal, [1,2,3,4])))))
    
    def test_set_dict(self):
        res = parse("% set a = {'b': 4, 'c': 5}")
        self.assertEqual(res, Set('a', DictDisplay(
            KeyDatumList(
                KeyDatum(Literal('b'),
                         Literal(4)),
                KeyDatum(Literal('c'),
                         Literal(5))
                )
            )))
        
    def test_set_attributeref(self):
        res = parse("% set a = b.c")
        self.assertEqual(res, Set('a', 
                                  AttributeRef(
                                      Identifier('b'), 
                                      Identifier('c'))))
        
    def test_set_subscription(self):
        res = parse("% set a = b[1]")
        self.assertEqual(res, Set('a', 
                                  Subscription(
                                      Identifier('b'), 
                                      ExpressionList(
                                          Literal(1)
                                          ))))
    
    def test_set_slice(self):
        res = parse("% set a = b[1:2]")
        self.assertEqual(res, Set('a', 
                                  SimpleSlicing(
                                      Identifier('b'), 
                                      Slice(
                                          Literal(1),
                                          Literal(2),
                                          ))))
                                      
    def test_set_extended_slice(self):
        res = parse("% set a = b[1:2:3]")
        self.assertEqual(res, Set('a', 
                                  ExtendedSlicing(
                                      Identifier('b'), 
                                      SliceList(
                                      Slice(
                                          Literal(1),
                                          Literal(2),
                                          Literal(3),
                                          )))))
        
    def test_set_call(self):
        res = parse("% set a = func()")
        self.assertEqual(res, Set('a',
            Call(Identifier('func'))))
        
    def test_set_call_args_simple(self):
        res = parse("% set a = func(4)")
        self.assertEqual(res, Set('a',
            Call(Identifier('func'), 
                 ArgumentList(PositionalArguments(Literal(4))))))
        
    def test_set_call_args_many(self):
        res = parse("% set a = func(4, a, foo='bar', baz='quux')")
        self.assertEqual(res, Set('a',
            Call(Identifier('func'), 
                 ArgumentList(
                     PositionalArguments(
                         Literal(4),
                         Identifier('a'),
                         ),
                     KeywordArguments(
                         KeywordItem('foo', Literal('bar')),
                         KeywordItem('baz', Literal('quux')),
                         ),
                     ))))
        
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
        
