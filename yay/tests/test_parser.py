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

from yay import parser
from yay.errors import ParseError
from yay.ast import *

from .base import bare_parse as parse
from .base import TestCase

import os


class TestParser(TestCase):

    def test_include(self):
        res = parse("""
        include 'foo.yay'
        """)
        self.assertEqual(res, Include(Literal('foo.yay')))

    def test_include_levels(self):
        res = parse("""
        a:
            include 'foo.yay'
        """)
        self.assertEqual(res, YayDict([
            ('a', Include(Literal('foo.yay')))
        ]))

    def test_comment(self):
        res = parse("""
        # i am a little teapot
        include 'foo.yay'
        # short and stout
        """)
        self.assertEqual(res, Include(Literal('foo.yay')))

    def test_set_integer_literal(self):
        res = parse("""
        set a = 2
        """)
        self.assertEqual(res, Set(Identifier('a'), Literal(2)))

    def test_set_string_literal(self):
        res = parse("""
        set a = 'foo'
        """)
        self.assertEqual(res, Set(Identifier('a'), Literal("foo")))

    def test_set_string_arithmetic(self):
        res = parse("""
        set a = 'foo ' + 'bar'
        """)
        self.assertEqual(
            res, Set(Identifier('a'), Add(Literal('foo '), Literal('bar'))))

    def test_set_float_literal(self):
        res = parse("""
        set a = 2.4
        """)
        self.assertEqual(res, Set(Identifier('a'), Literal(2.4)))

    def test_set_identifier(self):
        res = parse("""
        set a = b
        """)
        self.assertEqual(res, Set(Identifier('a'), Identifier('b')))

    def test_set_addition(self):
        res = parse("""
        set a = 2+2
        """)
        self.assertEqual(
            res, Set(Identifier('a'), Add(Literal(2), Literal(2))))

    def test_set_complex_expr(self):
        res = parse("""
        set a = (2+2)*5/12.0
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Divide(
                                      Multiply(
                                          ParentForm(
                                              Add(Literal(2), Literal(2)),
                                          ),
                                          Literal(5)),
                                      Literal(12.0),
                                  )))

    def test_set_list(self):
        res = parse("""
        set a = [1,2,3,4]
        """)
        self.assertEqual(
            res, Set(Identifier('a'), ListDisplay(ExpressionList(*map(Literal, [1, 2, 3, 4])))))

    def test_set_dict(self):
        res = parse("""
        set a = {'b': 4, 'c': 5}
        """)
        self.assertEqual(res, Set(Identifier('a'), DictDisplay(
            KeyDatumList(
                KeyDatum(Literal('b'),
                         Literal(4)),
                KeyDatum(Literal('c'),
                         Literal(5))
            )
        )))

    def test_set_attributeref(self):
        res = parse("""
        set a = b.c
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  AttributeRef(
                                      Identifier('b'),
                                      'c')))

    def test_set_subscription(self):
        res = parse("""
        set a = b[1]
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Subscription(
                                      Identifier('b'),
                                      Literal(1)
                                  )))

    def test_set_slice(self):
        res = parse("""
        set a = b[1:2]
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  SimpleSlicing(
                                      Identifier('b'),
                                      Slice(
                                          Literal(1),
                                          Literal(2),
                                      ))))

    def test_set_slice_lower_only(self):
        res = parse("""
        set a = b[1:]
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  SimpleSlicing(
                                      Identifier('b'),
                                      Slice(
                                          Literal(1),
                                          None,
                                      ))))

    def test_set_slice_upper_only(self):
        res = parse("""
        set a = b[:2]
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  SimpleSlicing(
                                      Identifier('b'),
                                      Slice(
                                          None,
                                          Literal(2),
                                      ))))

    def test_set_slice_stride(self):
        res = parse("""
        set a = b[1:2:3]
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  SimpleSlicing(
                                      Identifier('b'),
                                      Slice(
                                          Literal(1),
                                          Literal(2),
                                          Literal(3),
                                      ))))

    def test_set_call(self):
        res = parse("""
        set a = func()
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Call(Identifier('func'))))

    def test_set_call_args_1(self):
        res = parse("""
        set a = func(1)
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Call(Identifier('func'), [Literal(1)])))

    def test_set_call_args_1_trailing(self):
        res = parse("""
        set a = func(1,)
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Call(Identifier('func'), [Literal(1)])))

    def test_set_call_args_2_trailing(self):
        res = parse("""
        set a = func(1,2,)
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Call(Identifier('func'), [Literal(1), Literal(2)])))

    def test_set_call_kwargs(self):
        res = parse("""
        set a = func(arg1=True, arg2=identifier)
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Call(Identifier('func'), kwargs=KeywordArguments(
                                      Kwarg(Identifier('arg1'), Identifier('True')), Kwarg(Identifier('arg2'), Identifier('identifier'))))
                                  ))

    def test_set_parentheses(self):
        res = parse("""
        set a = (1,2,3)
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  ParentForm(ExpressionList(Literal(1), Literal(2), Literal(3)))))

    def test_set_parentheses_empty(self):
        res = parse("""
        set a = ()
        """)
        self.assertEqual(res, Set(Identifier('a'), ParentForm()))

    def test_set_not(self):
        res = parse("""
        set a = not b
        """)
        self.assertEqual(res, Set(Identifier('a'), Not(Identifier('b'))))

    def test_set_and(self):
        res = parse("""
        set a = b and c
        """)
        self.assertEqual(
            res, Set(Identifier('a'), And(Identifier('b'), Identifier('c'))))

    def test_set_or(self):
        res = parse("""
        set a = b or c
        """)
        self.assertEqual(
            res, Set(Identifier('a'), Or(Identifier('b'), Identifier('c'))))

    def test_set_conditional_expression(self):
        res = parse("""
        set a = b if c else d
        """)
        self.assertEqual(
            res, Set(Identifier('a'), ConditionalExpression(Identifier('c'), Identifier('b'), Identifier('d'))))

    def test_set_multiple(self):
        res = parse("""
        set a,b = c,d
        """)
        self.assertEqual(res, Set(
            TargetList(Identifier('a'), Identifier('b')),
            ExpressionList(Identifier('c'), Identifier('d'))))

    def test_set_multiple_trailing(self):
        res = parse("""
        set a,b, = c,d,
        """)
        self.assertEqual(res, Set(
            TargetList(Identifier('a'), Identifier('b')),
            ExpressionList(Identifier('c'), Identifier('d'))))

    def test_set_multiple_more(self):
        res = parse("""
        set a,b,c,d = c,d,b,a
        """)
        self.assertEqual(res, Set(
            TargetList(Identifier('a'), Identifier(
                'b'), Identifier('c'), Identifier('d')),
            ExpressionList(Identifier('c'), Identifier('d'), Identifier('b'), Identifier('a'))))

    def test_for(self):
        res = parse("""
        for a in b:
             - x
        """)
        self.assertEqual(
            res, For(Identifier('a'), Identifier('b'), YayList(YayScalar('x'))))

    def test_set_call_args_simple(self):
        res = parse("""
        set a = func(4)
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Call(Identifier('func'), [Literal(4)])))

    def test_set_call_args_many(self):
        res = parse("""
        set a = func(4, a, foo='bar', baz='quux')
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Call(Identifier('func'), [
                                      Literal(4),
                                      Identifier('a'),
                                  ], [
                                      Kwarg(Identifier('foo'), Literal('bar')),
                                      Kwarg(
                                          Identifier('baz'), Literal('quux')),
                                  ]
                                  )))

    def test_set_unary_minus(self):
        res = parse("""
        set a = -b
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  UnaryMinus(Identifier('b'))))

    def test_set_unary_plus(self):
        res = parse("""
        set a = +b
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Identifier('b')))

    def test_set_precedence_1(self):
        res = parse("""
        set a = b * c + d
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Add(Multiply(Identifier('b'), Identifier('c')),
                                      Identifier('d'))))

    def test_set_precedence_2(self):
        res = parse("""
        set a = b + c * d
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Add(Identifier('b'),
                                      Multiply(Identifier('c'), Identifier('d')))))

    def test_comparison_1(self):
        res = parse("""
        set a = b < c
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  LessThan(Identifier('b'), Identifier('c'))))

    def test_comparison_2(self):
        res = parse("""
        set a = b not in c
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  NotIn(Identifier('b'), Identifier('c'))))

    def test_emptydict(self):
        res = parse("""
            a: {}
        """)
        self.assertEqual(res, YayDict([('a', YayDict())]))

    def test_emptylist(self):
        res = parse("""
            a: []
        """)
        self.assertEqual(res, YayDict([('a', YayList())]))

    def test_simple_dict(self):
        res = parse("""
            a: b
        """)
        self.assertEqual(res, YayDict([('a', YayScalar('b'))]))

    def NOtest_simple_dict_trailing_whitespace(self):
        res = parse("a: b ")
        self.assertEqual(res, YayDict([('a', YayScalar('b'))]))

    def test_simple_dict_colon_in_value(self):
        self.assertRaises(ParseError, parse, """
            a: b: c
        """)

    def test_simple_dict_space(self):
        res = parse("""
            a : b
        """)
        self.assertEqual(res, YayDict([('a', YayScalar('b'))]))

    def test_two_item_dict(self):
        res = parse("""
        a: b
        c: d
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', YayScalar('d')),
        ]))

    def test_command_and_dict(self):
        res = parse("""
        include 'foo.yay'

        a: b
        """)
        self.assertEqual(res, Stanzas(
            Include(Literal('foo.yay')),
            YayDict([('a', YayScalar('b'))])))

    def test_nested_dict(self):
        res = parse("""
        a:
            b: c
        """)
        self.assertEqual(res, YayDict([
            ('a', YayDict([
                ('b', YayScalar('c'))
            ]))
        ]))

    def test_sample1(self):
        res = parse("""
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
        self.assertEqual(res, YayDict([
            ('key1', YayScalar('value1')),
            ('key2', YayScalar('value2')),
            ('key3', YayList(YayScalar('item1'), YayScalar('item2'), YayScalar('item3'))),
            ('key4', YayDict([
                ('key5', YayDict([
                    ('key6', YayScalar('key7')),
                ]))
            ])),
        ]))

    def test_list_of_dicts(self):
        res = parse("""
            a:
              - b
              - c: d
              - e
              """)
        self.assertEqual(res, YayDict([
            ('a', YayList(YayScalar('b'),
                          YayDict([
                              ('c', YayScalar('d'))
                          ]),
                          YayScalar('e')
                          ))
        ]))

    def test_template_1(self):
        res = parse("""
        a: b
        c: {{a}}
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', Identifier('a')),
        ]))

    def test_template_2(self):
        res = parse("""
        a: b
        c: hello {{a}}
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', YayMerged(YayScalar('hello '), Identifier('a'))),
        ]))

    def test_template_3(self):
        res = parse("""
        a: b
        c: {{a}} hello
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', YayMerged(Identifier('a'), YayScalar(' hello'))),
        ]))

    def test_template_4(self):
        res = parse("""
        a: b
        c: woo {{a}} hello
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', YayMerged(YayMerged(YayScalar("woo "), Identifier("a")), YayScalar(" hello")))
        ]))

    def test_template_5(self):
        res = parse("""
        a: b
        c: {{"this " + a + " that"}}
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', Add(Add(Literal('this '), Identifier('a')), Literal(" that")))
        ]))

    def test_template_6(self):
        res = parse("""
        a: b
        c: {{1.0 + 2}}
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', Add(Literal(1.0), Literal(2)))
        ]))

    def test_list_of_complex_dicts(self):
        res = parse("""
            a:
              - b
              - c:
                - e
                - f
            """)
        self.assertEqual(res, YayDict([
            ('a', YayList(
                YayScalar('b'),
                YayDict([('c', YayList(
                    YayScalar('e'),
                    YayScalar('f')
                ))])))]))
        self.assertEqual(res.resolve(), {
            'a': [
                'b',
                {'c': ['e', 'f']},
            ]
        })

    def test_list_of_multikey_dicts(self):
        res = parse("""
            a:
              - b
              - c: d
                e: f
              - g
              """)
        self.assertEqual(res, YayDict([
            ('a', YayList(YayScalar('b'), YayDict([
                ('c', YayScalar('d')),
                ('e', YayScalar('f'))
            ]), YayScalar('g')))
        ]))

    def test_list_of_dicts_with_lists_in(self):
        res = parse("""
            a:
             - b: c
               d:
                 - e
                 - f
                 - g
              """)
        self.assertEqual(res, YayDict([
            ('a', YayList(YayDict([
                ('b', YayScalar('c')),
                ('d', YayList(YayScalar('e'), YayScalar('f'), YayScalar('g')))
            ])))
        ]))
        self.assertEqual(res.resolve(), {'a': [
            {'b': 'c',
             'd': ['e', 'f', 'g'],
             }]})

    def test_mix(self):
        res = parse("""
        include 'foo.yay'

        bar:
            set a = 2
            for x in range(a):
                - {{x}}

        quux:
            - a
            - b
        """)
        self.assertEqual(res, Stanzas(
            Include(Literal('foo.yay')),
            YayDict([
                ('bar', Directives(
                    Set(Identifier('a'), Literal(2)),
                    For(Identifier('x'), Call(Identifier('range'), [
                        Identifier('a')]), YayList(Identifier('x')))
                    )),
                ('quux', YayList(YayScalar('a'), YayScalar('b')))
            ]),
        ))

    def test_extend_1(self):
        res = parse("""
        extend x:
            - a
            - b
            - c
        """)
        self.assertEqual(res, YayDict([
            ('x', YayExtend(YayList(YayScalar('a'), YayScalar('b'), YayScalar('c')))),
        ]))

    def test_extend_2(self):
        res = parse("""
        extend x:
            a: b
        """)
        self.assertEqual(res, YayDict([
            ('x', YayExtend(YayDict([
                ('a', YayScalar('b')),
            ])))
        ]))

    def test_extend_3(self):
        res = parse("""
        extend x:
            for a in b:
                - a
        """)
        self.assertEqual(res, YayDict([
            ('x', YayExtend(For(Identifier('a'), Identifier('b'), YayList(YayScalar('a'))))),
        ]))

    def test_extend_4(self):
        res = parse("""
        extend x: {{a}}
        """)
        self.assertEqual(res, YayDict([
            ('x', YayExtend(Identifier('a'))),
        ]))

    def test_list_comprehension_no_conditional(self):
        res = parse("""
        set a = [ x for x in y ]
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            ListDisplay(
                ListComprehension(Identifier('x'),
                                  ListFor(Identifier('x'),
                                          Identifier('y'))))))

    def test_list_comprehension_with_conditional(self):
        res = parse("""
        set a = [ x for x in y if z ]
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            ListDisplay(
                ListComprehension(Identifier('x'),
                                  ListFor(Identifier('x'),
                                          Identifier('y'),
                                          ListIf(Identifier('z')))))))

    def test_list_comprehension_with_conditional_repeated(self):
        res = parse("""
        set a = [ x for x in y if z if b ]
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            ListDisplay(
                ListComprehension(Identifier('x'),
                                  ListFor(Identifier('x'),
                                          Identifier('y'),
                                          ListIf(Identifier('z'),
                                                 iterator=ListIf(
                                                     Identifier('b'))
                                                 ))))))

    def test_set_comprehension_no_conditional(self):
        res = parse("""
        set a = { x for x in y }
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            SetDisplay(
                Comprehension(Identifier('x'),
                              CompFor(Identifier('x'),
                                      Identifier('y'))))))

    def test_set_comprehension_with_conditional(self):
        res = parse("""
        set a = { x for x in y if z }
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            SetDisplay(
                Comprehension(Identifier('x'),
                              CompFor(Identifier('x'),
                                      Identifier('y'),
                                      CompIf(Identifier('z')))))))

    def test_dict_comprehension_no_conditional(self):
        res = parse("""
        set a = { x : x for x in y }
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            DictDisplay(
                DictComprehension(Identifier('x'),
                                  Identifier('x'),
                                  CompFor(Identifier('x'),
                                          Identifier('y'))))))

    def test_dict_comprehension_with_conditional(self):
        res = parse("""
        set a = { x : x for x in y if z }
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            DictDisplay(
                DictComprehension(Identifier('x'),
                                  Identifier('x'),
                                  CompFor(Identifier('x'),
                                          Identifier('y'),
                                          CompIf(Identifier('z')))))))

    def test_dict_comprehension_with_conditional2(self):
        res = parse("""
        set a = { x : x for x in y if z if b }
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            DictDisplay(
                DictComprehension(Identifier('x'),
                                  Identifier('x'),
                                  CompFor(Identifier('x'),
                                          Identifier('y'),
                                          CompIf(Identifier('z'),
                                                 CompIf(Identifier('b'))))))))

    def test_generator_expression_no_conditional(self):
        res = parse("""
        set a = ( x for x in y )
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            GeneratorExpression(Identifier('x'),
                                CompFor(Identifier('x'),
                                        Identifier('y')))))

    def test_generator_expression_with_conditional(self):
        res = parse("""
        set a = ( x for x in y if z )
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            GeneratorExpression(Identifier('x'),
                                CompFor(Identifier('x'),
                                        Identifier('y'),
                                        CompIf(Identifier('z'))))))

    def test_old_lambda(self):
        res = parse("""
        set a = [x for x in y if lambda x: True]
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            ListDisplay(
                ListComprehension(Identifier('x'),
                                  ListFor(Identifier('x'),
                                          Identifier('y'),
                                          ListIf(LambdaForm(
                                              Identifier('True'),
                                              ParameterList(
                                                  DefParameter(
                                                      Identifier('x')
                                                  )))))))))

    def test_lambda_no_params(self):
        res = parse("""
        set a = lambda : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(Identifier('x'))))

    def test_lambda_with_param(self):
        res = parse("""
        set a = lambda b : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(params=ParameterList(DefParameter(Identifier('b'))),
                       expression=Identifier('x'))))

    def test_lambda_with_param_default(self):
        res = parse("""
        set a = lambda b=4 : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(
                params=ParameterList(
                    DefParameter(Identifier('b'), Literal(4))),
                expression=Identifier('x'))))

    def test_lambda_with_params(self):
        res = parse("""
        set a = lambda b, c : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(
                params=ParameterList(
                    DefParameter(
                        Identifier('b')), DefParameter(Identifier('c'))),
                expression=Identifier('x'))))

    def test_lambda_with_params_trailing(self):
        res = parse("""
        set a = lambda b, c, : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(
                params=ParameterList(
                    DefParameter(
                        Identifier('b')), DefParameter(Identifier('c'))),
                expression=Identifier('x'))))

    def test_lambda_with_param_sublists(self):
        res = parse("""
        set a = lambda b, (c,d) : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(params=ParameterList(
                DefParameter(Identifier('b')),
                DefParameter(Sublist(Identifier('c'),
                                     Identifier('d')))
            ),
                expression=Identifier('x'))))

    def test_lambda_with_param_sublists_trailing(self):
        res = parse("""
        set a = lambda b, (c,d,) : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(params=ParameterList(
                DefParameter(Identifier('b')),
                DefParameter(Sublist(Identifier('c'),
                                     Identifier('d')))
            ),
                expression=Identifier('x'))))

    def test_new(self):
        res = parse("""
        new foo:
            x: y
        """)
        self.assertEqual(res, New(
            Identifier('foo'),
            YayDict([('x', YayScalar('y'))]),
        ))

    def test_new_as(self):
        res = parse("""
            new Provisioner as foo:
                x: y
        """)
        self.assertEqual(res, YayDict([
            ('foo', New(
                Identifier('Provisioner'),
                YayDict([('x', YayScalar('y'))]),
            ))]))

    def test_prototype(self):
        res = parse("""
        prototype foo:
            x: y
        """)
        self.assertEqual(res, Ephemeral(Identifier('foo'), Prototype(
            YayDict([('x', YayScalar('y'))]),
        )))

    def test_if(self):
        res = parse("""
        if True:
            x: y
        """)
        self.assertEqual(
            res, If(Identifier('True'), YayDict([('x', YayScalar('y'))])))

    def test_if_else(self):
        res = parse("""
        if True:
            x: y
        else:
            x: z
        """)
        self.assertEqual(res, If(Identifier('True'),
                                 YayDict([('x', YayScalar('y'))]),
                                 YayDict([('x', YayScalar('z'))]),
                                 ))

    def test_if_elif(self):
        res = parse("""
        if True:
            x: y
        elif True:
            x: z
        elif True:
            x: a
        """)
        self.assertEqual(res,
                         If(Identifier('True'), YayDict([('x', YayScalar('y'))]),
                            If(Identifier('True'), YayDict([('x', YayScalar('z'))]),
                               If(Identifier('True'), YayDict([('x', YayScalar('a'))])))))

    def test_if_elif_else(self):
        res = parse("""
        if True:
            x: y
        elif True:
            x: z
        else:
            x: a
        """)
        self.assertEqual(res, If(Identifier('True'),
                                 YayDict([('x', YayScalar('y'))]),
                                 If(Identifier('True'), YayDict([('x', YayScalar('z'))]),
                                    YayDict([('x', YayScalar('a'))])
                                    )))

    def test_error_else(self):
        self.assertRaises(SyntaxError, parse, """
        else:
            x: y
        """)

    def test_search(self):
        res = parse("""
        search "foo"
        """)
        self.assertEqual(res, Search(Literal("foo")))

    def test_select(self):
        res = parse("""
        select foo:
            bar:
                - a
            baz:
                - b
            quux:
            froo:
        """)
        self.assertEqual(res, Select(Identifier("foo"),
                                     CaseList(
                                         Case("bar", YayList(YayScalar("a"))),
                                         Case("baz", YayList(YayScalar("b"))),
                                         Case('quux', YayScalar("")),
                                         Case('froo', YayScalar("")),
                                     )))

    def test_multiline_fold_simple(self):
        res = parse("""
        a: >
          foo bar baz
          quux quuux
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz quux quuux")),
        ]))

    def test_multiline_fold(self):
        res = parse("""
        a: >
          foo bar baz

          quux quuux
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz  quux quuux")),
        ]))

    def test_multiline_literal(self):
        res = parse("""
        a: |
          foo bar baz

          quux quuux


        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz\n\nquux quuux\n")),
        ]))

    def test_multiline_literal_complex(self):
        res = parse("""
        a:
            b: |
                l1
                l2
            c: x
        d: e
        """)
        self.assertEqual(res, YayDict([
            ('a', YayDict([
                ('b', YayScalar("l1\nl2\n")),
                ('c', YayScalar('x')),
            ])),
            ('d', YayScalar('e')),
        ]))

    def test_multiline_strip(self):
        res = parse("""
        a: |-
          foo bar baz

          quux quuux


        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz\n\nquux quuux")),
        ]))

    def test_multiline_keep(self):
        res = parse("""
        a: |+
          foo bar baz

          quux quuux


        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz\n\nquux quuux\n\n\n")),
        ]))

    def test_multiline_template(self):
        res = parse("""
        a: >
          foo {{bar}} baz
          quux
        """)
        self.assertEqual(res, YayDict([
            ('a', YayMerged(
                YayMerged(
                    YayScalar('foo '),
                    Identifier('bar')),
                YayScalar(' baz quux')))]))

    def test_multiline_template_ateol(self):
        res = parse("""
        a: >
          foo {{bar}}
          quux
        """)
        self.assertEqual(res, YayDict([
            ('a', YayMerged(
                YayMerged(
                    YayScalar('foo '),
                    Identifier('bar')),
                YayScalar(' quux')))]))

    def test_python_line_continuation(self):
        res = parse(r"""
        if x == y and \
           c == d:
             - x
        """)
        self.assertEqual(res, If(
            And(
                Equal(Identifier('x'), Identifier('y')),
                Equal(Identifier('c'), Identifier('d'))),
            YayList(YayScalar('x'))
        )
        )

    def test_yaml_line_continuation(self):
        res = parse(r"""
        a: b \
        x: y
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b \\')),
            ('x', YayScalar('y')),
        ]))

    def test_code_in_list(self):
        res = parse(r"""
        a:
          - a
          - b
          for i in j:
            - {{i}}
          - c
        """)
        self.assertEqual(res, YayDict([
            ('a', Stanzas(
                YayList(
                    YayScalar('a'),
                    YayScalar('b'),
                ),
                For(Identifier('i'),
                    Identifier('j'),
                    YayList(
                        Identifier('i')
                    )
                    ),
                YayList(
                    YayScalar('c'),
                )
            )
            )
        ]))

    def test_for_in_list_in_for(self):
        res = parse(r"""
        a:
          for x in y:
            - a
            for i in j:
              - {{i}}
            - c
        """)
        self.assertEqual(res, YayDict([
            ('a', For(Identifier('x'),
                      Identifier('y'),
                      Stanzas(
                          YayList(
                              YayScalar('a'),
                          ),
                          For(Identifier('i'),
                              Identifier('j'),
                              YayList(
                                  Identifier('i')
                              )
                              ),
                          YayList(
                              YayScalar('c'),
                          )
                      )))
        ]))

    def test_string_conversion(self):
        res = parse("""
        set a = `foo`
        """)
        self.assertEqual(res, Set(
            Identifier('a'), StringConversion(Identifier('foo'))))
