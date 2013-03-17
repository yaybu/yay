import unittest
from yay import parser
from yay.ast import *

import os

def parse(value):
    p = parser.Parser()
    return p.parse(value, debug=0)

class TestParser(unittest.TestCase):

    def test_include(self):
        res = parse("""
        include 'foo.yay'
        """)
        self.assertEqual(res, Include(Literal('foo.yay')))

    def test_comment(self):
        res = parse("""
        # i am a little teapot
        include 'foo.yay'
        # short and stout
        """)
        self.assertEqual(res, Stanzas(
            Comment("# i am a little teapot"),
            Include(Literal('foo.yay')),
            Comment("# short and stout"),
            ))

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
        self.assertEqual(res, Set(Identifier('a'), Expr(Literal('foo '), Literal('bar'), '+')))

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
        self.assertEqual(res, Set(Identifier('a'), Expr(Literal(2), Literal(2), '+')))

    def test_set_complex_expr(self):
        res = parse("""
        set a = (2+2)*5/12.0
        """)
        self.assertEqual(res, Set(Identifier('a'),
            Expr(
                Expr(
                    ParentForm(
                            Expr(Literal(2), Literal(2), '+'),
                        ),
                    Literal(5),
                    '*'),
                Literal(12.0),
                '/')
            ))

    def test_set_list(self):
        res = parse("""
        set a = [1,2,3,4]
        """)
        self.assertEqual(res, Set(Identifier('a'), ListDisplay(ExpressionList(*map(Literal, [1,2,3,4])))))

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

    def test_set_extended_slice(self):
        res = parse("""
        set a = b[1:2:3]
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  ExtendedSlicing(
                                      Identifier('b'),
                                      SliceList(
                                      Slice(
                                          Literal(1),
                                          Literal(2),
                                          Literal(3),
                                          )))))

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

    def test_set_call_kwargs(self):
        res = parse("""
        set a = func(arg1=True, arg2=identifier)
        """)
        self.assertEqual(res, Set(Identifier('a'),
            Call(Identifier('func'), kwargs=KeywordArguments(Kwarg(Identifier('arg1'), Identifier('True')), Kwarg(Identifier('arg2'), Identifier('identifier'))))
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
        self.assertEqual(res, Set(Identifier('a'), Expr(Identifier('b'), Identifier('c'), 'and')))

    def test_set_or(self):
        res = parse("""
        set a = b or c
        """)
        self.assertEqual(res, Set(Identifier('a'), Expr(Identifier('b'), Identifier('c'), 'or')))

    def test_set_conditional_expression(self):
        res = parse("""
        set a = b if c else d
        """)
        self.assertEqual(res, Set(Identifier('a'), ConditionalExpression(Identifier('c'), Identifier('b'), Identifier('d'))))

    def test_set_multiple(self):
        res = parse("""
        set a,b = c,d
        """)
        self.assertEqual(res, Set(
            TargetList(Identifier('a'), Identifier('b')),
            ExpressionList(Identifier('c'), Identifier('d'))))

    def test_for(self):
        res = parse("""
        for a in b:
             - x
        """)
        self.assertEqual(res, For(Identifier('a'), Identifier('b'), YayList(YayScalar('x'))))

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
                         Kwarg(Identifier('baz'), Literal('quux')),
                         ]
                     )))

    def test_set_unary_minus(self):
        res = parse("""
        set a = -b
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  UnaryMinus(Identifier('b'))))

    def test_set_precedence_1(self):
        res = parse("""
        set a = b * c + d
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Expr(Expr(Identifier('b'), Identifier('c'), '*'),
                                       Identifier('d'),
                                       '+')))

    def test_set_precedence_2(self):
        res = parse("""
        set a = b + c * d
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Expr(Identifier('b'),
                                       Expr(Identifier('c'), Identifier('d'), '*'),
                                       '+')))

    def test_comparison_1(self):
        res = parse("""
        set a = b < c
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Expr(Identifier('b'), Identifier('c'), '<')))

    def test_comparison_2(self):
        res = parse("""
        set a = b not in c
        """)
        self.assertEqual(res, Set(Identifier('a'),
                                  Expr(Identifier('b'), Identifier('c'), 'not in')))

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
            ('c', Template(Identifier('a'))),
        ]))

    def test_template_2(self):
        res = parse("""
        a: b
        c: hello {{a}}
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', YayMerged(YayScalar('hello '), Template(Identifier('a')))),
        ]))

    def test_template_3(self):
        res = parse("""
        a:b
        c: {{a}} hello
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', YayMerged(Template(Identifier('a')), YayScalar(' hello'))),
        ]))

    def test_template_4(self):
        res = parse("""
        a:b
        c: woo {{a}} hello
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', YayMerged(YayScalar('woo '), Template(Identifier('a')), YayScalar(' hello'))),
        ]))

    def test_template_5(self):
        res = parse("""
        a:b
        c: {{"this " + a + " that"}}
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', Template(Expr(Expr(Literal('this '), Identifier('a'), '+'), Literal(" that"), "+")))
        ]))

    def test_template_6(self):
        res = parse("""
        a:b
        c: {{1.0 + 2}}
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar('b')),
            ('c', Template(Expr(Literal(1.0), Literal(2), "+")))
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
                For(Identifier('x'), Call(Identifier('range'), [Identifier('a')])
                              , YayList(Template(Identifier('x'))))
                )),
                ('quux', YayList(YayScalar('a'), YayScalar('b')))
                ]),
        ))

    def test_configure(self):
        res = parse("""
        configure x:
            y: z
        """)
        self.assertEqual(res, Configure(
            'x', YayDict([
                ('y', YayScalar('z')),
                ])))

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
            ('x', YayExtend(Template(Identifier('a')))),
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

    def test_lambda_no_params(self):
        res = parse("""
        set a = lambda : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(Identifier('x'))))

    def test_lambda_with_params(self):
        res = parse("""
        set a = lambda b : x
        """)
        self.assertEqual(res, Set(
            Identifier('a'),
            LambdaForm(params=ParameterList(DefParameter(Identifier('b'))),
                       expression=Identifier('x'))))


    def test_create(self):
        res = parse("""
        create foo
            x: y
        """)
        self.assertEqual(res, Create(
            Identifier('foo'),
            YayDict([('x', YayScalar('y'))]),
            ))

    def test_if(self):
        res = parse("""
        if True:
            x: y
        """)
        self.assertEqual(res, If(Identifier('True'), YayDict([('x', YayScalar('y'))])))

    def test_if_else(self):
        res = parse("""
        if True:
            x: y
        else:
            x: z
        """)
        self.assertEqual(res, If(Identifier('True'),
                                 YayDict([('x', YayScalar('y'))]),
                                 else_=YayDict([('x', YayScalar('z'))]),
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
        self.assertEqual(res, If(Identifier('True'),
                                 YayDict([('x', YayScalar('y'))]),
                                 ElifList(
                                     Elif(Identifier('True'), YayDict([('x', YayScalar('z'))])),
                                     Elif(Identifier('True'), YayDict([('x', YayScalar('a'))])),
                                 )))


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
                                 ElifList(
                                     Elif(Identifier('True'), YayDict([('x', YayScalar('z'))]))
                                     ),
                                 YayDict([('x', YayScalar('a'))])
                                 ))

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
        """)
        self.assertEqual(res, Select(Identifier("foo"),
                                     CaseList(
                                     Case("bar", YayList(YayScalar("a"))),
                                     Case("baz", YayList(YayScalar("b"))),
                                     )))

    def test_create(self):
        res = parse("""
        create "Compute":
            foo: bar
        """)
        self.assertEqual(res, Create(Literal("Compute"),
                                     YayDict([
                                         ('foo', YayScalar('bar')),
                                         ])))
    def test_fold(self):
        res = parse("""
        a: >
          foo bar baz
          quux quuux
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz\nquux quuux\n")),
            ]))

    def test_fold_breaks(self):
        res = parse("""
        a: >
          foo bar baz

          quux quuux
        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz\nquux quuux\n")),
            ]))

    def test_block_clip(self):
        res = parse("""
        a: |
          foo bar baz

          quux quuux


        """)
        self.assertEqual(res, YayDict([
        ('a', YayScalar("foo bar baz\n\nquux quuux\n")),
        ]))

    def test_block_indents(self):
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

    def test_block_strip(self):
        res = parse("""
        a: |-
          foo bar baz

          quux quuux


        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz\n\nquux quuux")),
            ]))

    def test_block_keep(self):
        res = parse("""
        a: |+
          foo bar baz

          quux quuux


        """)
        self.assertEqual(res, YayDict([
            ('a', YayScalar("foo bar baz\n\nquux quuux\n\n\n")),
            ]))

    def test_python_line_continuation(self):
        res = parse(r"""
        if x == y and \
           c == d:
             - x
        """)
        self.assertEqual(res, If(
            Expr(
                Expr(Identifier('x'),
                     Identifier('y'),
                     '=='),
                Expr(Identifier('c'),
                     Identifier('d'),
                     '=='),
                "and"),
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



