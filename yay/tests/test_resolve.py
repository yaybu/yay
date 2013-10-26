# Copyright 2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .base import parse, resolve, TestCase
from yay import errors, ast
from yay.errors import ParseError


class TestYayDict(TestCase):

    def test_very_lazy(self):
        res = resolve("""
            a: b
            b: {{ a }}
            a: c
            """)
        self.assertEqual(res['b'], "c")

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
            for x in range:
                - {{x}}

        quux:
            - a
            - b
        """)

        self.assertEqual(res, {
            "range": [1, 2],
            "bar": [1, 2],
            "quux": ['a', 'b'],
        })

    def test_nested_dict(self):
        res = resolve("""
        a:
            b: c
        """)
        self.assertEqual(res, {"a": {"b": "c"}})

    def test_extend_lookup(self):
        """
        This test has 3 sections - a, b, c
        The parse will create 3 YayDicts and then merge c into b, then b into a
        If the merge is naive then it will cause predecessors to be lost.
        You can't just do v.predecessor, instead you need to find the tip of the predecessor ancestry
        """
        res = resolve("""
            foo:
                a: 1
                b: 1
                c: 1

            bar: {{ foo }}

            bar:
                d: 1

            """)
        self.assertEqual(res['bar']['a'], 1)
        self.assertEqual(res['bar']['d'], 1)

    def test_extend_lookup_lazier(self):
        """
        This test exists as a counterpoint to ``test_extend_lookup`` as we
        notcied that it was key-order-sensitive
        """
        res = resolve("""
            bar: {{ foo }}

            foo:
                a: 1
                b: 1
                c: 1

            bar:
                d: 1
            """)
        self.assertEqual(res['bar']['a'], 1)
        self.assertEqual(res['bar']['d'], 1)

    def test_for_on_dict(self):
        res = resolve("""
            test:
              foo:
                sitename: www.foo.com
              bar:
                sitename: www.bar.com
              baz:
                sitename: www.baz.com

            out:
              for x in test:
                 - {{ x }}

            out2:
              for x in test:
                 - {{ test[x].sitename }}

            """)

        self.assertEqual(res['out'], ['foo', 'bar', 'baz'])
        self.assertEqual(
            res['out2'], ['www.foo.com', 'www.bar.com', 'www.baz.com'])

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

    def test_here(self):
        res = resolve("""
            foo:
                site: www.example.com
                sitedir: /var/www/{{ here.site }}

            foo:
                site: www.example.org
            """)
        self.assertEqual(res['foo']['sitedir'], '/var/www/www.example.org')


class TestEmptyDocument(TestCase):

    def test_empty_document(self):
        res = resolve("")

    def test_include_empty_document(self):
        res = resolve("""
            include "foo"
            """,
                      foo="",
                      )


class TestYayList(TestCase):

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
                "d": ["e", "f", "g"],
            }]
        })

    def test_nested_for(self):
        res = resolve("""
        range:
          - 1
          - 2

        bar:
            for x in range:
              for y in range:
                - {{x + y}}
        """)
        self.assertEquals(res['bar'], [2, 3, 3, 4])

    def test_as_list(self):
        res = parse("""
            foo:
              - 1
              - 2
            """)
        self.assertEqual(res.foo.as_list(), [1, 2])
        self.assertEqual(res.foo.get_type(), "streamish")

    def test_as_iterable(self):
        res = parse("""
            foo:
              - 1
              - 2
            """)
        self.assertEqual(list(res.foo.as_iterable()), [1, 2])


class TestTemplate(TestCase):

    def test_escaping(self):
        res = resolve("""
            foo: {{ "{{ foo }}" }}
            """)
        self.assertEqual(res['foo'], "{{ foo }}")

    def test_template_variable_between_scalars(self):
        self.assertEqual(
            resolve("name: doug\nbar: hello {{ name }} !\n")['bar'],
            "hello doug !"
        )

    def test_template_multiple_variables(self):
        self.assertEqual(
            resolve(
                "name: doug\nname2: steve\nbar: {{ name }} and {{ name2 }}!\n")['bar'],
            "doug and steve!"
        )

    def test_multiple_expressions(self):
        t = parse("""
            sitename: example.com
            log_location: /var/log/{{ sitename }}
            """)
        self.assertEqual(
            t.get_key("log_location").as_string(), "/var/log/example.com")
        self.assertEqual(t.get_type(), "dictish")
        self.assertEqual(t.get_key("log_location").get_type(), "scalarish")


class TestIdentifier(TestCase):

    def test_syntax_error(self):
        self.assertRaises(ParseError, parse, """
            foo: 5
            bar: {{ @foo }}
            """)

    def test_get_bool(self):
        t = parse("""
            foo: 5
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_int(), 5)
        self.assertEqual(t.get_key("bar").get_type(), "scalarish")

    def test_get_bool_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_bool)

    def test_get_bool_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_bool(default=True), True)

    def test_get_integer(self):
        t = parse("""
            foo: 5
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_int(), 5)
        self.assertEqual(t.get_key("bar").get_type(), "scalarish")

    def test_get_integer_type_error(self):
        t = parse("""
            foo: five
            bar: {{ foo}}
            """)
        self.assertRaises(errors.TypeError, t.get_key("bar").as_int)

    def test_get_integer_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_int)

    def test_get_integer_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_int(default=5), 5)

    def test_get_float(self):
        t = parse("""
            foo: 5.5
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_float(), 5.5)

    def test_get_float_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_float)

    def test_get_float_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_float(default=5.5), 5.5)

    def test_get_number(self):
        t = parse("""
            foo: 5.5
            baz: 5
            bar: {{ foo }}
            qux: {{ baz }}
            """)
        self.assertEqual(t.get_key("bar").as_number(), 5.5)
        self.assertEqual(t.get_key("qux").as_number(), 5)

    def test_get_number_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_number)

    def test_get_number_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_number(default=5.5), 5.5)
        self.assertEqual(t.get_key("bar").as_number(default=5), 5)

    def test_get_safe_string(self):
        t = parse("""
            foo: hello
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_safe_string(), "hello")

    def test_get_safe_string_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_safe_string)

    def test_get_safe_string_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(
            t.get_key("bar").as_safe_string(default="default"), "default")

    def test_get_string(self):
        t = parse("""
            foo: hello
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_string(), "hello")

    def test_get_string_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_string)

    def test_get_string_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(
            t.get_key("bar").as_string(default="default"), "default")

    def test_get_list(self):
        t = parse("""
            foo: []
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_list(), [])

    def test_get_list_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_list)

    def test_get_list_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_list(default=[]), [])

    def test_get_iterable(self):
        t = parse("""
            foo: []
            bar: {{ foo }}
            """)
        self.assertEqual(list(t.get_key("bar").as_iterable()), [])

    def test_get_iterable_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_iterable)

    def test_get_iterable_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_iterable(default=[]), [])

    def test_get_dict(self):
        t = parse("""
            foo: {}
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_dict(), {})

    def test_get_dict_nomatching(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertRaises(errors.NoMatching, t.get_key("bar").as_dict)

    def test_get_iterable_default(self):
        t = parse("""
            bar: {{ foo }}
            """)
        self.assertEqual(t.get_key("bar").as_dict(default={}), {})

    def test_forloop(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            bar:
              for f in foo:
                -  {{ f }}
            """)
        results = t.get_key("bar").get_iterable()
        self.assertEqual([r.resolve() for r in results], [1, 2, 3])

    def test_as_dict(self):
        t = parse("""
            foo: {{ other_identifier }}
            """)
        self.assertEqual(t.get_key("foo").as_dict({}), {})
        self.assertEqual(t.foo.as_dict({}), {})


class TestSequence(TestCase):

    def test_get_key(self):
        g = self._parse("""
            foo:
              - 1
              - 2
              - 3
            """)
        self.assertEqual(g.get_key("foo").get_key(2).resolve(), 3)


class TestLiteral(TestCase):

    def test_syntax_error(self):
        # FIXME: I would be happier if this was a errors.ParseError
        # SyntaxError comes from within lexer.
        self.assertRaises(SyntaxError, parse, """
            foo: {{ 0'.3 }}
            """)

    def test_get_integer(self):
        t = parse("foo: {{ 5 }}\n")
        self.assertEqual(t.get_key("foo").as_int(), 5)

    def test_as_dict(self):
        t = parse("""
            foo: {{ 5 }}
            """)
        self.assertRaises(errors.TypeError, t.foo.as_dict)

    def test_as_list(self):
        t = parse("""
            foo: {{ 5 }}
            """)
        self.assertRaises(errors.TypeError, t.foo.as_list)

    def test_as_iterable(self):
        t = parse("""
            foo: {{ 5 }}
            """)
        self.assertRaises(errors.TypeError, t.foo.as_iterable)


class TestParentForm(TestCase):

    def test_empty_parent(self):
        t = parse("foo: {{ () }}\n")
        self.assertEqual(t.get_key("foo").resolve(), [])


class TestUnaryMinus(TestCase):

    def test_simple_case(self):
        t = parse("""
            foo: -1
            """)

        self.assertEqual(t.get_key("foo").as_int(), -1)

    def test_via_identifier(self):
        t = parse("""
            foo: 1
            bar: {{ -foo }}
            """)

        self.assertEqual(t.get_key("bar").as_int(), -1)

    def test_type_error_via_identifier(self):
        t = parse("""
            foo: []
            bar: {{ -foo }}
            """)

        self.assertRaises(errors.TypeError, t.get_key("bar").as_int)


class TestInvert(TestCase):

    def test_simple_case(self):
        t = parse("""
            foo: {{ ~5 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), -6)


class TestEqual(TestCase):

    def test_equals(self):
        res = resolve("bar: {{ 1 == 2 }}\n")
        self.assertEqual(res, {"bar": False})

    def test_variables_equals(self):
        res = resolve("""
          a: 1
          b: 1
          c: {{ a == b}}
          """)
        self.assertEqual(res['c'], True)

    def test_different_types(self):
        res = resolve("""
          bar: {{ 1 == "one" }}
          """)
        self.assertEqual(res['bar'], False)


class TestNotEqual(TestCase):

    def test_not_equals(self):
        res = resolve("bar: {{ 1 != 2}}\n")
        self.assertEqual(res, {"bar": True})

    def test_different_types(self):
        res = resolve("""
          bar: {{ 1 != "one" }}
          """)
        self.assertEqual(res['bar'], True)


class TestGreaterThan(TestCase):

    def test_gt(self):
        res = resolve("""
            bar: {{ 2 > 1 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_not_gt(self):
        res = resolve("""
            bar: {{ 1 > 2 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_eq(self):
        res = resolve("""
            bar: {{ 1 > 1 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_lhs_neg(self):
        res = resolve("""
            bar: {{ -1 > 1 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_rhs_neg(self):
        res = resolve("""
            bar: {{ 1 > -1 }}
            """)
        self.assertEqual(res['bar'], True)


class TestLessThan(TestCase):

    def test_gt(self):
        res = resolve("""
            bar: {{ 2 < 1 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_not_gt(self):
        res = resolve("""
            bar: {{ 1 < 2 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_eq(self):
        res = resolve("""
            bar: {{ 1 < 1 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_lhs_neg(self):
        res = resolve("""
            bar: {{ -1 < 1 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_rhs_neg(self):
        res = resolve("""
            bar: {{ 1 < -1 }}
            """)
        self.assertEqual(res['bar'], False)


class TestGreaterThanEqual(TestCase):

    def test_gt(self):
        res = resolve("""
            bar: {{ 2 >= 1 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_not_gt(self):
        res = resolve("""
            bar: {{ 1 >= 2 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_eq(self):
        res = resolve("""
            bar: {{ 1 >= 1 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_lhs_neg(self):
        res = resolve("""
            bar: {{ -1 >= 1 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_rhs_neg(self):
        res = resolve("""
            bar: {{ 1 >= -1 }}
            """)
        self.assertEqual(res['bar'], True)


class TestLessThanEqual(TestCase):

    def test_gt(self):
        res = resolve("""
            bar: {{ 2 <= 1 }}
            """)
        self.assertEqual(res['bar'], False)

    def test_not_gt(self):
        res = resolve("""
            bar: {{ 1 <= 2 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_eq(self):
        res = resolve("""
            bar: {{ 1 <= 1 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_lhs_neg(self):
        res = resolve("""
            bar: {{ -1 <= 1 }}
            """)
        self.assertEqual(res['bar'], True)

    def test_rhs_neg(self):
        res = resolve("""
            bar: {{ 1 <= -1 }}
            """)
        self.assertEqual(res['bar'], False)


class TestAdd(TestCase):

    def test_plus(self):
        t = parse("""
            foo: {{ 1 + 1 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 2)

    def test_add_strings(self):
        t = parse("""
            foo: {{ "foo" + "bar" }}
            """)
        self.assertEqual(t.get_key('foo').as_string(), 'foobar')

    def test_type_error(self):
        t = parse("""
            foo: {{ [] + {} }}
            """)
        self.assertRaises(errors.TypeError, t.get_key("foo").as_int)


class TestSubtract(TestCase):

    def test_minus(self):
        t = parse("""
            foo: {{ 1 - 1 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)

    def test_negative(self):
        t = parse("""
            foo: {{ 1 - 2 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), -1)

    def test_negative_negative(self):
        t = parse("""
            foo: {{ 1 - -2 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 3)

    def test_subtract_strings(self):
        t = parse("""
            foo: {{ "foo" - "foo" }}
            """)
        self.assertRaises(errors.TypeError, t.get_key("foo").resolve)


class TestMultiply(TestCase):

    def test_multiply(self):
        t = parse("""
            foo: {{ 2 * 3 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 6)

    def test_multiply_neg(self):
        t = parse("""
            foo: {{ -2 * 3 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), -6)

    def test_multiply_strings(self):
        t = parse("""
            foo: {{ "foo" * "foo" }}
            """)
        self.assertRaises(errors.TypeError, t.get_key("foo").resolve)


class TestDivide(TestCase):

    def test_divide(self):
        t = parse("""
            foo: {{ 8 / 2 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 4)

    def test_divide_pep238(self):
        """ Yay has python 3 style PEP238 division """
        t = parse("""
            foo: {{ 5 / 2 }}
            """)
        self.assertEqual(t.get_key("foo").resolve(), 2.5)

    def test_divide_strings(self):
        t = parse("""
            foo: {{ "foo" / "foo" }}
            """)
        self.assertRaises(errors.TypeError, t.get_key("foo").resolve)

    def test_divide_by_zero(self):
        t = parse("""
            foo: {{ 5 / 0 }}
            """)
        self.assertRaises(errors.ZeroDivisionError, t.get_key("foo").resolve)

    def test_divide_by_zero_via_vars(self):
        t = parse("""
            bar: 5
            baz: 0
            foo: {{ bar / baz }}
            """)
        self.assertRaises(errors.ZeroDivisionError, t.get_key("foo").resolve)


class TestFloorDivide(TestCase):

    def test_divide(self):
        t = parse("""
            foo: {{ 5 // 2 }}
            """)
        self.assertEqual(t.get_key("foo").resolve(), 2)

    def test_divide_strings(self):
        t = parse("""
            foo: {{ "foo" // "foo" }}
            """)
        self.assertRaises(errors.TypeError, t.get_key("foo").resolve)

    def test_divide_by_zero(self):
        t = parse("""
            foo: {{ 5 // 0 }}
            """)
        self.assertRaises(errors.ZeroDivisionError, t.get_key("foo").resolve)

    def test_divide_by_zero_via_vars(self):
        t = parse("""
            bar: 5
            baz: 0
            foo: {{ bar // baz }}
            """)
        self.assertRaises(errors.ZeroDivisionError, t.get_key("foo").resolve)


class TestMod(TestCase):

    def test_no_remainder(self):
        t = parse("""
            foo: {{ 8 % 8 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)

    def test_1_remainder(self):
        t = parse("""
            foo: {{ 9 % 8 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 1)

    def test_7_remainder(self):
        t = parse("""
            foo: {{ 15 % 8 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 7)

    def test_8_remainder(self):
        t = parse("""
            foo: {{ 16 % 8 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)

    def test_divide_strings(self):
        t = parse("""
            foo: {{ "foo" % "foo" }}
            """)
        self.assertRaises(errors.TypeError, t.get_key("foo").resolve)


class TestRshift(TestCase):

    def test_rshift(self):
        t = parse("""
            foo: {{ 6 >> 2 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 1)


class TestLshift(TestCase):

    def test_lshift(self):
        t = parse("""
            foo: {{ 6 << 2 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 24)


class TestXor(TestCase):

    def test_xor(self):
        t = parse("""
            foo: {{ 6 ^ 2 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 6 ^ 2)


class TestBitwiseAnd(TestCase):

    def test_bitwise_and_0(self):
        t = parse("""
            foo: {{ 8 & 7 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)

    def test_bitwise_and_8(self):
        t = parse("""
            foo: {{ 15 & 8 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 8)


class TestAnd(TestCase):

    def test_and_true_true(self):
        t = parse("""
            foo: {{ 1 and 1 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 1)

    def test_and_false_true(self):
        t = parse("""
            foo: {{ 0 and 1 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)

    def test_and_true_false(self):
        t = parse("""
            foo: {{ 1 and 0 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)

    def test_and_false_false(self):
        t = parse("""
            foo: {{ 0 and 0 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)


class TestBitwiseOr(TestCase):

    def test_bitwise_or(self):
        t = parse("""
            foo: {{ 8 | 2 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 10)


class TestElse(TestCase):

    def test_else(self):
        res = resolve("""
            foo:
                bar: 42
                wibble: 22
            bar: {{ foo.baz else foo.bar }}
            baz: {{ foo.baz else foo.qux else foo.bar }}
            qux: {{ foo.wibble else foo.baz }}
            """)
        self.assertEqual(res['bar'], 42)
        self.assertEqual(res['baz'], 42)
        self.assertEqual(res['qux'], 22)

    def test_else_empty_list(self):
        res = resolve("""
            foo: {{ a else [] }}
            """)
        self.assertEqual(res['foo'], [])

    def test_else_empty_dict(self):
        res = resolve("""
            foo: {{ a else {} }}
            """)
        self.assertEqual(res['foo'], {})

    def test_else_string(self):
        res = resolve("""
            foo: {{ a else "foo" }}
            """)
        self.assertEqual(res['foo'], "foo")

    def test_else_include(self):
        res = resolve("""
            include (a else "foo") + "_inc"
            """,
                      foo_inc="hello: world\n")
        self.assertEqual(res['hello'], 'world')


class TestNotIn(TestCase):

    def test_not_in(self):
        t = parse("""
            fruit:
              - apple
              - pear
            foo: {{ "potato" not in fruit }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 1)


class TestPower(TestCase):

    def test_power_literals(self):
        t = parse("""
            foo: {{ 2 ** 2 }}
            """)

        self.assertEqual(t.get_key("foo").as_int(), 4)

    def test_power_ident1(self):
        t = parse("""
            foo: 2
            qux: {{ 2 ** foo }}
            """)

        self.assertEqual(t.get_key("qux").as_int(), 4)

    def test_power_ident2(self):
        t = parse("""
            foo: 2
            bar: {{ foo ** 2 }}
            """)

        self.assertEqual(t.get_key("bar").as_int(), 4)

    def test_type_error(self):
        t = parse("""
            foo: {{ 2 ** [] }}
            """)

        self.assertRaises(errors.TypeError, t.get_key("foo").as_int)


class TestNot(TestCase):

    def test_not_true(self):
        t = parse("""
            foo: {{ not 0 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 1)

    def test_not_false(self):
        t = parse("""
            foo: {{ not 1 }}
            """)
        self.assertEqual(t.get_key("foo").as_int(), 0)


class TestConditionalExpression(TestCase):

    def test_eval_true(self):
        t = parse("""
            foo: {{ "foo" if 1 else "bar" }}
            """)
        self.assertEqual(t.get_key("foo").resolve(), "foo")

    def test_eval_false(self):
        t = parse("""
            foo: {{ "foo" if 0 else "bar" }}
            """)
        self.assertEqual(t.get_key("foo").resolve(), "bar")


class TestListDisplay(TestCase):

    def test_empty(self):
        t = parse("""
          foo: {{ [] }}
          """)
        self.assertEqual(t.get_key("foo").resolve(), [])

    def test_list_comprehension(self):
        res = resolve("""
            foo: {{ [a+1 for a in range(5)] }}
            """)
        self.assertEqual(res['foo'], [1, 2, 3, 4, 5])


class TestDictDisplay(TestCase):

    def test_empty(self):
        t = parse("""
            foo: {{ {} }}
            """)
        self.assertEqual(t.get_key("foo").resolve(), {})

    def test_none(self):
        t = parse("""
            foo:
            bar: baz
            """)
        self.assertEqual(t.get_key("foo").resolve(), "")


class TestDict(TestCase):

    def test_as_dict(self):
        g = parse("""
            foo:
                bar: baz
            """)
        self.assertEqual(g.foo.as_dict(), {"bar": "baz"})


class TestAttributeRef(TestCase):

    def test_attributeref(self):
        res = resolve("""
            a:
              b: hello
            bar: {{ a.b }}
            """)
        self.assertEqual(res['bar'], 'hello')


class TestSubscription(TestCase):

    def test_subscription_string(self):
        res = resolve("""
            a:
              b: hello
            bar: {{ a['b'] }}
            """)
        self.assertEqual(res['bar'], 'hello')

    def test_subscription_variable(self):
        res = resolve("""
            a:
              b: hello
            c: b
            bar: {{ a[c] }}
            """)
        self.assertEqual(res['bar'], 'hello')

    def test_subscription_variable(self):
        res = resolve("""
            a:
              b: hello
            c: b
            bar: {{ a[c] }}
            """)
        self.assertEqual(res['bar'], 'hello')

    def test_subscription_of_list(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            bar: {{ foo[1] }}
            """)
        self.assertEqual(t.get_key("bar").as_int(), 2)

    def test_subscription_of_list_with_identifier(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            qux: 0

            bar: {{ foo[qux] }}
            """)
        self.assertEqual(t.get_key("bar").as_int(), 1)

    def test_subscription_of_list_nested(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            bar: {{ foo[foo[0]] }}
            """)
        self.assertEqual(t.get_key("bar").as_int(), 2)


class TestFor(TestCase):

    def test_for_emit_dict(self):
        res = resolve("""
            foolist:
              - name: john
                age: 28
              - name: simon
                age: 41
              - name: sandra
                age: 47

            bar:
                maxage: 40

            baz:
                for p in foolist if p.age < bar.maxage:
                    - nameage: {{p.name}}{{p.age}}
                      agename: {{p.age}}{{p.name}}
            """)
        self.assertEqual(
            res['baz'], [{'nameage': 'john28', 'agename': '28john'}])

    def test_for_if_1(self):
        res = resolve("""
            nodes:
              - name: foo
              - name: baz
              - name: 5

            test:
                for node in nodes if node.name == 5:
                    - {{node}}
            """)
        self.assertEqual(res['test'], [{'name': 5}])

    def test_for_if_2(self):
        res = resolve("""
            nodes:
              - name: foo
              - name: baz
              - name: 5

            foo: foo

            test:
                for node in nodes if node.name == foo:
                    - {{node}}
            """)
        self.assertEqual(res['test'], [{'name': 'foo'}])

    def test_for_on_for(self):
        res = resolve("""
            foo:
              - 1
              - 2
              - 3

            bar:
                for f in foo:
                    - {{ f }}

            baz:
                for b in bar:
                    - {{ b }}
            """)
        self.assertEqual(res['bar'], [1, 2, 3])
        self.assertEqual(res['baz'], [1, 2, 3])

    def test_nested_foreach(self):
        res = resolve("""
            project:
              - name: monkeys
                flavour: bob
                environments:
                  - name: staging
                    host: ririn
                  - name: production
                    host: cloud
              - name: badgers
                flavour: george
                environments:
                 - name: staging
                   host: ririn
                 - name: production
                   host: cloud

            test:
              for project in project:
                for env in project.environments:
                   - name: {{ project.name }}
                     env: {{ env.name }}
            """)

        self.assertEqual(res['test'], [
            {'name': 'monkeys', 'env': 'staging'},
            {'name': 'monkeys', 'env': 'production'},
            {'name': 'badgers', 'env': 'staging'},
            {'name': 'badgers', 'env': 'production'},
        ])

    def test_complicated_chained_for(self):
        res = resolve("""
            wibble:
              for i in range(1):
                - {{ i }}

                for i in range(2,3):
                    - {{ i }}

                - {{ i + 1}}

                if 1:
                    - {{ 3 }}

                - {{ i + 2 }}

                if 0:
                    - {{ 1 }}

                - {{ i + 3 }}

                select i:
                    0:
                      - {{ i }}

            """)
        self.assertEqual(res["wibble"], [0, 2, 1, 3, 2, 3, 0])

    def test_adjacent_list_and_dict(self):
        self.assertRaises(errors.TypeError, resolve, """
            a: 10
            for i in range(a):
                - {{ i }}
            """)


class TestSlicing(TestCase):

    def test_simple_slicing(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            bar: {{ foo[0:2] }}
            """)
        self.assertEqual(t.get_key("bar").resolve(), [1, 2])

    def test_slice_simple(self):
        res = resolve("""
            lista:
                - 1
                - 2
                - 3
                - 4
                - 5

            listb: {{ lista[0:2] }}

            listc:
              for x in listb:
                - {{ x }}

            listd:
              for x in listb:
                - {{ x }}

            """)

        self.assertEqual(res['listb'], [1, 2])
        self.assertEqual(res['listc'], [1, 2])
        self.assertEqual(res['listd'], [1, 2])

    def test_slice_stride(self):
        res = resolve("""
            lista:
                - 1
                - 2
                - 3
                - 4
                - 5

            listb: {{ lista[0:5:2] }}

            """)

        self.assertEqual(res['listb'], [1, 3, 5])


class TestPythonClassMock(ast.PythonClass):

    def apply(self):
        assert self.params.get_key('foo').as_string() == 'bar'
        assert self.params['foo'].as_string() == 'bar'
        assert self.params.foo.as_string() == 'bar'

        self.members.set('hello', 'world')


class TestPythonClass(TestCase):

    builtins = {
        "TestPythonClassMock": ast.PythonClassFactory(TestPythonClassMock),
    }

    def test_simple_class(self):
        res = self._resolve("""
            foo:
              new TestPythonClassMock:
                  foo: bar
            """)
        self.assertEqual(res['foo']['hello'], 'world')

    def test_alias(self):
        res = self._resolve("""
            set MyAlias = TestPythonClassMock
            foo:
              new MyAlias:
                  foo: bar
            """)
        self.assertEqual(res['foo']['hello'], 'world')


class TestPrototype(TestCase):

    def test_prototype_not_in_output(self):
        self.assertEqual(resolve("""
            foo: bar
            prototype NotInOutput:
                hello: world
            bar: foo
            """), dict(foo="bar", bar="foo"))

    def test_simple_prototype(self):
        self.assertEqual(resolve("""
            prototype Simple:
                hello: world
            example:
                new Simple:
                    param: foo
            """), dict(example=dict(hello="world", param="foo")))

    def test_simple_prototype_with_as(self):
        self.assertEqual(resolve("""
            prototype Simple:
                hello: world
            new Simple as example:
                param: foo
            """), dict(example=dict(hello="world", param="foo")))

    def test_use_params(self):
        self.assertEqual(resolve("""
            prototype WithParams:
                hello: foo-{{ self.param }}-bar
            new WithParams as example:
                param: foo
        """), dict(example=dict(hello="foo-foo-bar", param="foo")))


class TestNew(TestCase):

    def test_new_on_scalar(self):
        self.assertRaises(errors.TypeError, self._resolve, """
            Bar: hello
            foo:
              new Bar:
                  foo: bar
            """)

    def test_new_on_list(self):
        self.assertRaises(errors.TypeError, self._resolve, """
            Bar:
              - hello
            foo:
              new Bar:
                  foo: bar
            """)

    def test_new_on_identifier(self):
        self.assertRaises(errors.TypeError, self._resolve, """
            Bar: {{ baz }}
            baz: hello

            foo:
              new Bar:
                  foo: bar
            """)


class TestPythonCall(TestCase):

    def test_range(self):
        res = resolve("""
            upper: 3
            foo: {{ range(upper) }}
            bar: {{ range(1, upper+1) }}
            """)
        self.assertEqual(res['foo'], [0, 1, 2])
        self.assertEqual(res['bar'], [1, 2, 3])

    def test_iter_on_range(self):
        res = resolve("""
            a: 5
            b:
                for i in range(a):
                    - {{ -i }}
            """)
        self.assertEqual(res['b'], [0, -1, -2, -3, -4])

    def test_replace(self):
        res = resolve("""
            teststring: foo bar baz
            replacedstring: {{ replace(teststring, " ", "-") }}
            """)
        self.assertEqual(res['replacedstring'], 'foo-bar-baz')


class TestMacroCall(TestCase):

    def test_macro(self):
        res = resolve("""
            macro SomeMacro:
                - SomeItem:
                    name: {{ name }}
                - SomeOtherItem:
                    name: {{ name }}

            extend resources:
                call SomeMacro:
                      name: foo

            extend resources:
                call SomeMacro:
                      name: foobar
            """)

        self.assertEqual(res['resources'], [
            {"SomeItem": {"name": "foo"}},
            {"SomeOtherItem": {"name": "foo"}},
            {"SomeItem": {"name": "foobar"}},
            {"SomeOtherItem": {"name": "foobar"}},
        ])

    def test_macro_call_in_expression(self):
        res = resolve("""
            macro SomeMacro:
                - SomeItem:
                    name: {{ name }}
                - SomeOtherItem:
                    name: {{ name }}

            extend resources: {{ SomeMacro(name='foo') }}
            extend resources: {{ SomeMacro(name='foobar')}}
            """)

        self.assertEqual(res['resources'], [
            {"SomeItem": {"name": "foo"}},
            {"SomeOtherItem": {"name": "foo"}},
            {"SomeItem": {"name": "foobar"}},
            {"SomeOtherItem": {"name": "foobar"}},
        ])

    def test_macro_call_in_different_files(self):
        res = resolve("""
            include 'file1'
            include 'file2'
            """,
            file1="""
            macro SomeMacro:
                - SomeItem:
                    name: {{ name }}
                - SomeOtherItem:
                    name: {{ name }}
            """,
            file2="""
            extend resources:
                call SomeMacro:
                      name: foo

            extend resources: {{ SomeMacro(name='foobar') }}
            """)

        self.assertEqual(res['resources'], [
            {"SomeItem": {"name": "foo"}},
            {"SomeOtherItem": {"name": "foo"}},
            {"SomeItem": {"name": "foobar"}},
            {"SomeOtherItem": {"name": "foobar"}},
        ])

    def test_macro_call_within_loop(self):
        res = resolve("""
            macro SomeMacro:
                - SomeItem:
                    name: {{ name }}
                - SomeOtherItem:
                    name: {{ name }}

            names:
                - foo
                - bar

            extend resources:
                for name in names:
                    call SomeMacro:
                        name: {{ name }}
            """)

        self.assertEqual(res["resources"], [
            {"SomeItem": {"name": "foo"}},
            {"SomeOtherItem": {"name": "foo"}},
            {"SomeItem": {"name": "bar"}},
            {"SomeOtherItem": {"name": "bar"}},
        ])

    def test_nested_macro(self):
        res = resolve("""
            macro SomeMacro:
                - SomeItem:
                    name: {{ name }}

            macro SomeOtherMacro:
                call SomeMacro:
                    name: {{ name }}

            extend resources:
                call SomeOtherMacro:
                    name: hoju
            """)

        self.assertEqual(res["resources"], [
            {"SomeItem": {"name": "hoju"}},
        ])

    def test_mapping_macro(self):
        res = resolve("""
            macro SomeMacro:
                SomeKey: {{ some_value }}

            call SomeMacro:
                some_value: foo
            """)

        self.assertEqual(res["SomeKey"], "foo")


class TestExtend(TestCase):

    def test_simple_extend(self):
        t = parse("""
            foo:
              - 1
              - 2

            extend foo:
              - 1
            """)
        self.assertEqual(t.get_key("foo").resolve(), [1, 2, 1])

    def test_extend(self):
        res = resolve("""
            resources:
                - Foo:
                     bar: baz
            extend resources:
                 - Qux:
                      bar: baz
            """)
        self.assertEquals(res['resources'], [
            {"Foo": {"bar": "baz"}},
            {"Qux": {"bar": "baz"}}
        ])

    def test_extend(self):
        res = resolve("""
            a: []
            extend foo: []
            extend bar: []
            baz: []
            extend qux: []
            """)
        self.assertEquals(res, {
            "a": [],
            "foo": [],
            "bar": [],
            "baz": [],
            "qux": [],
        })

    def test_extend_list_with_variable(self):
        res = resolve("""
            someval: julian
            somelist: []
            extend somelist:
              - {{ someval }}
            """)
        self.assertEqual(res['somelist'], ['julian'])


class TestInclude(TestCase):

    def test_simple_include(self):
        res = resolve("""
            include 'foo'
            """,
            foo="""
            hello: world
            """)
        self.assertEqual(res, {"hello": "world"})

    def test_include_with_extends(self):
        res = resolve("""
            include 'foo'
            extend resources:
             - 3
            """,
            foo="""
            resources:
              - 1
              - 2
            """)
        self.assertEqual(res, {"resources": [1, 2, 3]})

    def test_include_include(self):
        res = resolve("""
            include 'foo'
            """,
            foo="""
            include 'bar'
            """,
            bar="""
            hello: world
            """)
        self.assertEqual(res, {"hello": "world"})

    def test_include_include_2(self):
        res = resolve("""
            include 'foo'
            hello: world
            """,
            foo="""
            include 'bar'
            hello: quark
            wibble: wobble
            """,
            bar="""
            hello: qux
            foo: bar
            """)
        self.assertEqual(
            res, {"wibble": "wobble", "hello": "world", "foo": "bar"})

    def test_magic_1(self):
        res = resolve("""
            include "magic_1_1"
            include foo
            """,
            magic_1_1="""
            foo: magic_1_2
            """,
            magic_1_2="""
            bar: its a kind of magic
            """)
        self.assertEqual(res['bar'], 'its a kind of magic')

    def test_magic_2(self):
        res = resolve("""
            include test
            test: magic_2_1
            """,
            magic_2_1="""
            lol: it works
            """)
        self.assertEqual(res['lol'], 'it works')

    def test_multiple_lazy_includes(self):
        res = resolve("""
            include foo
            include "magic_1_1"
            include "magic_1_2"
            foo: lol_2
            """,
            magic_1_1="""
            foo: lol_1
            """,
            magic_1_2="""
            foo: lol_2
            """,
            lol_1="""
            bar: one
            """,
            lol_2="""
            bar: two
            """)
        self.assertEqual(res['bar'], 'two')

    def test_simple_nested_include(self):
        self._add("mem://example.yay", """
            foo: bar
            """)
        res = self._resolve("""
            foo:
                include "mem://example.yay"
            """)
        self.assertEqual(res['foo'], {"foo": "bar"})

    def test_simple_nested_include_surrounded(self):
        self._add("mem://example.yay", """
            foo: bar
            """)
        res = self._resolve("""
            foo:
                bar: wibble
                include "mem://example.yay"
                baz: quux
            """)
        self.assertEqual(
            res['foo'], {"foo": "bar", "bar": "wibble", "baz": "quux"})

    def test_include_based_on_var(self):
        self._add("mem://example.yay", """
           foo: bar
           """)
        res = self._resolve("""
            test: example
            include "mem://" + test + ".yay"
            """)
        self.assertEqual(res['foo'], 'bar')

    def test_include_based_on_var_twice(self):
        self._add("mem://example.yay", """
           foo: bar
           """)
        self._add("mem://example.2.yay", """
            qux: quux
            """)
        res = self._resolve("""
            test: example
            include "mem://" + test + ".2.yay"
            include "mem://" + test + ".yay"
            """)
        self.assertEqual(res['foo'], 'bar')
        self.assertEqual(res['qux'], 'quux')

    def test_include_var(self):
        self._add("mem://example.yay", """
           foo: bar
           """)
        res = self._resolve("""
            test: mem://example.yay
            include test
            """)
        self.assertEqual(res['foo'], 'bar')


class TestSelect(TestCase):

    def test_select(self):
        res = resolve("""
            foo: baz
            qux:
                select foo:
                  bar:
                    - a
                  baz:
                    - b
            """)

        self.assertEqual(res['qux'], ['b'])

    def test_select_sameline(self):
        res = resolve("""
            foo: baz
            qux:
                select foo:
                  baz: []
            """)

        self.assertEqual(res['qux'], [])

    def test_iter_over_select(self):
        res = resolve("""
            foo: baz
            qux:
                select foo:
                  bar:
                    - a
                  baz:
                    - b
            quux:
              for i in qux:
                - {{ i }}
            """)

        self.assertEqual(res['quux'], ['b'])

    def test_subscript_over_select(self):
        res = resolve("""
            foo: baz
            qux:
                select foo:
                  bar:
                    foo: a
                  baz:
                    foo: b

            quux: {{ qux['foo'] }}
            """)

        self.assertEqual(res['quux'], 'b')

    def test_integer_keys(self):
        res = resolve("""
            a: 10
            b:
                select a:
                    10: bar
                    20: quux
            """)
        self.assertEqual(res['b'], 'bar')


class TestIf(TestCase):

    def test_if(self):
        res = resolve("""
        x: 0
        a: c

        if x == 0:
            a: b
        """)
        self.assertEqual(res['a'], 'b')

    def test_if_else_true(self):
        res = resolve("""
        x: 0
        a: c
        if x == 0:
            a: b
        else:
            a: d
        """)
        self.assertEqual(res['a'], 'b')

    def test_if_else_false(self):
        res = resolve("""
        x: 0
        a: c
        if x == 1:
            a: b
        else:
            a: d
        """)
        self.assertEqual(res['a'], 'd')

    def test_if_elif_true(self):
        res = resolve("""
        x: 0
        a: c
        if x == 0:
            a: b
        elif x == 1:
            a: d
        """)
        self.assertEqual(res['a'], 'b')

    def test_if_elif_false(self):
        res = resolve("""
        x: 2
        a: c
        if x == 0:
            a: b
        elif x == 1:
            a: d
        """)
        self.assertEqual(res['a'], 'c')

    def test_if_elif_other_true(self):
        res = resolve("""
        x: 1
        a: c
        if x == 0:
            a: b
        elif x == 1:
            a: d
        """)
        self.assertEqual(res['a'], 'd')

    def test_mapping_conditional(self):
        res = resolve("""
            selector: hey

            if selector == "hey":
                foo:
                    hey:
                        baz: 2

            foo:
              quux: 3
            """)
        self.assertEqual(res['foo']['hey']['baz'], 2)
        self.assertEqual(res['foo']['quux'], 3)

    def test_complicated_nesting(self):
        res = resolve("""
            lol: foo

            if lol:
                bar: baz

            if bar == 'baz':
                lol: zinga
            """)

        self.assertEqual(res['lol'], 'zinga')

    def test_if_within_dict(self):
        res = resolve("""
            lol:
                foo: bar
                if 1:
                    baz: qux
                quux: zap
            """)

        self.assertEqual(
            res['lol'], {'foo': 'bar', 'baz': 'qux', 'quux': 'zap'})


class TestYayScalar(TestCase):

    def test_resolve(self):
        res = resolve("""
            foo: 1
            """)
        self.assertEqual(res['foo'], 1)

    def test_bool(self):
        t = parse("""
            foo: 1
            """)
        self.assertEqual(t.get_key('foo').as_bool(), True)

    # def test_bool_type_error(self):
    #    t = parse("""
    #        foo: bar
    #        """)
    #    self.assertRaises(errors.TypeError, t.get_key('foo').as_bool)

    def test_int(self):
        res = parse("""
            foo: 1
            """)
        self.assertEqual(res.get_key('foo').as_int(), 1)

    def test_int_type_error(self):
        t = parse("""
            foo: bar
            """)
        self.assertRaises(errors.TypeError, t.get_key('foo').as_int)

    def test_float(self):
        res = parse("""
            foo: 1.5
            """)
        self.assertEqual(res.get_key('foo').as_float(), 1.5)

    def test_float_type_error(self):
        t = parse("""
            foo: bar
            """)
        self.assertRaises(errors.TypeError, t.get_key('foo').as_float)


class TestSet(TestCase):

    def test_set(self):
        res = resolve("""
            set foo = "Simple expression"
            set bar = foo
            quux: {{ bar }}
            """)
        self.assertEqual(res, {"quux": "Simple expression"})

    def test_set_function(self):
        res = resolve("""
            set foo = range(5)
            quux: {{ foo }}
            """)
        self.assertEqual(res, {"quux": [0, 1, 2, 3, 4]})

    def test_set_list(self):
        res = resolve("""
            set foo = [1,2,3,4,5]
            quux: {{ foo }}
            """)
        self.assertEqual(res, {"quux": [1, 2, 3, 4, 5]})

    def test_set_dict(self):
        res = resolve("""
            set foo = {'a': 'b'}
            quux: {{ foo.a }}
            """)
        self.assertEqual(res, {"quux": 'b'})

    def test_set_within_mapping(self):
        res = resolve("""
            foo:
                set bar = "baz"
                qux: {{ bar }}
            """)
        self.assertEqual(res['foo']['qux'], 'baz')

    def test_set_self(self):
        res = resolve("""
            foo:
                set self = here

                sitename: www.example.com
                sitedir: /var/www/{{ self.sitename }}

                wakeup_urls:
                    - http//{{ self.sitename }}/

                settings:
                    DSN: postgres//{{ self.sitename }}
            """)

        self.assertEqual(res['foo']['wakeup_urls'], ["http//www.example.com/"])
        self.assertEqual(
            res['foo']['settings'], {"DSN": "postgres//www.example.com"})

    def test_set_in_for(self):
        res = resolve("""
            foo:
                for i in range(2):
                    set j = i + 1
                    - {{ j }}
            """)
        self.assertEqual(res['foo'], [1, 2])


class TestPythonicWrapper(TestCase):

    def setUp(self):
        self.graph = parse("""
            foo: 1
            bar: 2.0
            baz:
               hello: bonjour
            qux: a string
            quux:
                - fruit: apple
                - fruit: pear
            """)

    def test_attr_access(self):
        self.assertEqual(self.graph.foo.resolve(), 1)

    def test_nested_attr_access_is_pythonic(self):
        self.assertTrue(isinstance(self.graph.baz.hello, ast.PythonicWrapper))

    def test_nested_attr_access(self):
        self.assertEqual(self.graph.baz.hello.as_string(), "bonjour")

    def test_subscription(self):
        self.assertEqual(self.graph['baz']['hello'].as_string(), "bonjour")

    def test_float(self):
        self.assertEqual(float(self.graph.bar), 2.0)

    def test_float_default(self):
        self.assertEqual(self.graph.ribbon.quilt.as_float(5.0), 5.0)

    def test_int(self):
        self.assertEqual(int(self.graph.foo), 1)

    def test_int_default(self):
        self.assertEqual(self.graph.ribbon.quilt.as_int(5), 5)

    def test_str(self):
        self.assertEqual(str(self.graph.qux), "a string")

    def test_str_default(self):
        self.assertEqual(
            self.graph.ribbon.quilt.as_string("default"), "default")

    def test_dir(self):
        self.assertEqual(dir(self.graph.baz), ["hello"])

    def test_iter(self):
        it = iter(self.graph.quux)
        self.assertEqual(str(next(it).fruit), "apple")
        self.assertEqual(str(next(it).fruit), "pear")


class TestSearchPath(TestCase):

    def test_openers_search_pre(self):
        self._add("mem://foodir/example.yay", """
            foo: bar
            """)
        res = self._resolve("""
            yay:
                searchpath:
                  - {{ 'mem://foodir/' }}
            include "example.yay"
            """)
        self.assertEqual(res['foo'], 'bar')

    def test_openers_search_post(self):
        self._add("mem://foodir/example.yay", """
            foo: bar
            """)
        res = self._resolve("""
            include "example.yay"
            yay:
                searchpath:
                  - {{ 'mem://foodir/' }}
            """)
        self.assertEqual(res['foo'], 'bar')

    def test_openers_search_mid(self):
        self._add("mem://foodir/example.yay", """
            foo: bar
            """)
        res = self._resolve("""
            yay:
                searchpath:
                  - {{ 'mem://bardir/' }}
            include "example.yay"
            yay:
                extend searchpath:
                  - {{ 'mem://foodir/' }}
            """)
        self.assertEqual(res['foo'], 'bar')


class TestExpressionParsing(TestCase):

    def test_simple_lookup(self):
        g = self._parse("""
            a: 1
            b: 2
            """)

        self.assertEqual(g.parse_expression("a").resolve(), 1)
        self.assertEqual(g.parse_expression("b").resolve(), 2)

    def test_maths_in_expression(self):
        g = self._parse("""
            idx: 2
            somelist:
              - 1
              - 2
            """)
        self.assertEqual(g.parse_expression("somelist[idx-1]").resolve(), 2)


class TestRegression(TestCase):

    def test_foo(self):
        res = self._resolve("""
            somekey:
                - a: - "{{ 1 }}"
                for i in [] if i == "True":
                  - foo
            """)


class TestLabels(TestCase):

    def test_labels(self):
        res = self._parse("""
           resources:
            - Link:
                name: /etc/toremovelink
                policy: remove
            """)
        name = res.get_key("resources").get_key(
            0).get_key("Link").get_key("name")
        self.assertEqual(name.get_labels(), set([]))

    def test_labels_secret(self):
        res = self._parse("""
           resources:
            - Link:
                name: /etc/toremovelink
                policy: remove
            """, labels=("secret", ))
        name = res.get_key("resources").get_key(
            0).get_key("Link").get_key("name")
        self.assertEqual(name.get_labels(), set(["secret"]))
        self.assertEqual(name.as_safe_string(), "*****")

    def test_labels_secret_then_not_secret(self):
        res = self._parse("""
            name: tommy
            """, labels=("secret", ))
        res.loads("""
            foo: hello, {{ name }}
            """)
        foo = res.get_key("foo")
        self.assertEqual(foo.get_labels(), set(["secret"]))
        self.assertEqual(foo.as_safe_string(), "hello, *****")

    def test_labels_not_secret_then_secret(self):
        res = self._parse("""
            foo: hello, {{ name }}
            """)
        res.loads("""
            name: tommy
            """, labels=("secret", ))
        foo = res.get_key("foo")
        self.assertEqual(foo.get_labels(), set(["secret"]))
        self.assertEqual(foo.as_safe_string(), "hello, *****")

    def test_as_safe_string_default(self):
        g = self._parse("""
            foo: 1
            """)
        self.assertEqual(g.bar.as_safe_string(default="foo"), "foo")

    def test_as_safe_string_no_matching(self):
        g = self._parse("""
            foo: 1
            """)
        self.assertRaises(errors.NoMatching, g.bar.as_safe_string)


class TestStanzas(TestCase):

    def test_lots_of_fors(self):
        res = resolve("""
            resources:
              - a
              for i in range(1):
                  - b
              for j in range(1):
                  - c
              - d
            """)
        self.assertEqual(res['resources'], ['a', 'b', 'c', 'd'])


class TestOpeners(TestCase):
    pass

    # def test_openers_package_compat(self):
        # res = resolve("""
            #% include "package://yay.tests/fixtures/hello_world.yay"
            #""")
        #self.assertEqual(res['hello'], 'world')

    # def test_openers_config(self):
        # res = resolve("""
            # configure openers:
                # packages:
                    # index: http://b.pypi.python.org/simple
                # memory:
                    # example:
                        # hello: world

            #% include 'mem://example'
            #""")

        #self.assertEqual(res['hello'], 'world')
