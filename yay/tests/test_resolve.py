import unittest
from yay import parser
from yay.ast import *

def resolve(value):
    #print repr(parser.parse(value, debug=0))
    return Root(parser.parse(value, debug=0)).resolve()

class TestResolver(unittest.TestCase):

    def test_nested_dict(self):
        res = resolve("""
        a:
            b: c
        """)
        self.assertEqual(res, {"a": {"b": "c"}})

    def test_sample1(self):
        res = resolve("""
        key1: value1

        key2: value2

        key3:
          - item1
          - item2
          - item3

        key4:
            key5:
                key6: key7
        """)
        self.assertEqual(res, {
            "key1": "value1",
            "key2": "value2",
            "key3": ["item1", "item2", "item3"],
            "key4": {
                "key5": {
                    "key6": "key7",
                    }
                }
            })

    def test_list_of_dicts(self):
        res = resolve("""
            a:
              - b
              - c: d
              - e
              """)
        self.assertEqual(res, {"a": [
          "b",
          {"c": "d"},
          "e"
          ]})

    def test_list_of_complex_dicts(self):
        res = resolve("""
            a:
              - b
              - c:
                - e
                - f
            """)
        self.assertEqual(res, {
          "a": [
            "b",
            {"c": ["e", "f"]},
          ]})

    def test_list_of_multikey_dicts(self):
        res = resolve("""
            a:
              - b
              - c: d
                e: f
              - g
              """)
        self.assertEqual(res, {"a": [
          "b",
          {"c": "d", "e": "f"},
          "g",
          ]})

    def test_list_of_dicts_with_lists_in(self):
        res = resolve("""
            a:
             - b: c
               d:
                 - e
                 - f
                 - g
              """)
        self.assertEqual(res, {
          "a": [{
              "b": "c",
              "d": [ "e", "f", "g" ],
              }]
          })

    def test_simple_overlay(self):
        res = resolve("""
        foo:
          a: b

        foo:
          c: d
        """)
        self.assertEqual(res, {
            "foo": {"a": "b", "c": "d"},
            })

    def test_mix(self):
        res = resolve("""
        range:
          - 1
          - 2

        bar:
            % for x in range
                - {{x}}

        quux:
            - a
            - b
        """)

        self.assertEqual(res, {
            "range": ['1', '2'],
            "bar": ['1', '2'],
            "quux": ['a', 'b'],
            })

    def test_expr_equals(self):
        res = resolve("bar: {{ 1 == 2}}\n")
        self.assertEqual(res, {"bar": 'False'})

    def test_expr_not_equals(self):
        res = resolve("bar: {{ 1 != 2}}\n")
        self.assertEqual(res, {"bar": 'True'})

    def test_expr_variables_equals(self):
        res = resolve("""
          a: 1
          b: 1
          c: {{ a == b}}
          """)
        self.assertEqual(res['c'], 'True')

    def test_nested_for(self):
        # FIXME: WE WANT TO DO MATHS HERE
        res = resolve("""
        range:
          - 1
          - 2

        bar:
            % for x in range
              % for y in range
                - {{x + y}}
        """)
        self.assertEquals(res['bar'], ['11', '12', '21', '22'])
