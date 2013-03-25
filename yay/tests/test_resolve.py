import unittest2
from .base import parse, resolve
from yay import errors
from yay.parser import ParseError


class TestYayDict(unittest2.TestCase):

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

        self.assertEqual(res['out'], ['bar', 'baz', 'foo'])
        self.assertEqual(res['out2'], ['www.bar.com', 'www.baz.com', 'www.foo.com'])

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


class TestYayList(unittest2.TestCase):

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


class TestTemplate(unittest2.TestCase):

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
          resolve("name: doug\nname2: steve\nbar: {{ name }} and {{ name2 }}!\n")['bar'],
          "doug and steve!"
          )

    def test_multiple_expressions(self):
        t = parse("""
            sitename: example.com
            log_location: /var/log/{{ sitename }}
            """)
        self.assertEqual(t.get("log_location").as_string(), "/var/log/example.com")


class TestIdentifier(unittest2.TestCase):

    def test_syntax_error(self):
        self.assertRaises(ParseError, parse, """
            foo: 5
            bar: {{ @foo }}
            """)

    def test_get_integer(self):
        t = parse("""
            foo: 5
            bar: {{ foo }}
            """)
        self.assertEqual(t.get("bar").as_int(), 5)

    def test_get_integer_type_error(self):
        t = parse("""
            foo: five
            bar: {{ foo}}
            """)
        self.assertRaises(errors.TypeError, t.get("bar").as_int)

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
        results = t.get("bar").as_iterable()
        self.assertEqual([r.resolve() for r in results], [1,2,3])


class TestLiteral(unittest2.TestCase):

    def test_syntax_error(self):
        # FIXME: I would be happier if this was a errors.ParseError
        # SyntaxError comes from within lexer.
        self.assertRaises(SyntaxError, parse, """
            foo: {{ 0'.3 }}
            """)

    def test_get_integer(self):
        t = parse("foo: {{ 5 }}\n")
        self.assertEqual(t.get("foo").as_int(), 5)


class TestParentForm(unittest2.TestCase):

    def test_empty_parent(self):
        t = parse("foo: {{ () }}\n")
        self.assertEqual(t.get("foo").resolve(), [])


class TestPower(unittest2.TestCase):

    def test_power_literals(self):
        t = parse("""
            foo: {{ 2 ** 2 }}
            """)

        self.assertEqual(t.get("foo").as_int(), 4)

    def test_power_ident1(self):
        t = parse("""
            foo: 2
            qux: {{ 2 ** foo }}
            """)

        self.assertEqual(t.get("qux").as_int(), 4)

    def test_power_ident2(self):
        t = parse("""
            foo: 2
            bar: {{ foo ** 2 }}
            """)

        self.assertEqual(t.get("bar").as_int(), 4)

    def test_type_error(self):
        t = parse("""
            foo: {{ 2 ** [] }}
            """)

        self.assertRaises(errors.TypeError, t.get("foo").as_int)


class TestUnaryMinus(unittest2.TestCase):

    def test_simple_case(self):
        t = parse("""
            foo: -1
            """)

        self.assertEqual(t.get("foo").as_int(), -1)

    def test_via_identifier(self):
        t = parse("""
            foo: 1
            bar: {{ -foo }}
            """)

        self.assertEqual(t.get("bar").as_int(), -1)

    def test_type_error_via_identifier(self):
        t = parse("""
            foo: []
            bar: {{ -foo }}
            """)

        self.assertRaises(errors.TypeError, t.get("bar").as_int)


class TestExpression(unittest2.TestCase):

    def test_type_error(self):
        t = parse("""
            foo: {{ [] + {} }}
            """)
        self.assertRaises(errors.TypeError, t.get("foo").as_int)

    def test_equals(self):
        res = resolve("bar: {{ 1 == 2}}\n")
        self.assertEqual(res, {"bar": False})

    def test_not_equals(self):
        res = resolve("bar: {{ 1 != 2}}\n")
        self.assertEqual(res, {"bar": True})

    def test_variables_equals(self):
        res = resolve("""
          a: 1
          b: 1
          c: {{ a == b}}
          """)
        self.assertEqual(res['c'], True)

    def test_plus(self):
        t = parse("""
            foo: {{ 1 + 1 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 2)

    def test_minus(self):
        t = parse("""
            foo: {{ 1 - 1 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 0)

    def test_multiply(self):
        t = parse("""
            foo: {{ 2 * 3 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 6)

    def test_divide(self):
        t = parse("""
            foo: {{ 8 / 2 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 4)

    def test_xor(self):
        t = parse("""
            foo: {{ 6 ^ 2}}
            """)
        self.assertEqual(t.get("foo").as_int(), 6 ^ 2)
    def test_and_true_true(self):
        t = parse("""
            foo: {{ 1 and 1 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 1)

    def test_and_false_true(self):
        t = parse("""
            foo: {{ 0 and 1 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 0)

    def test_and_true_false(self):
        t = parse("""
            foo: {{ 1 and 0 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 0)

    def test_and_false_false(self):
        t = parse("""
            foo: {{ 0 and 0 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 0)


class TestOr(unittest2.TestCase):

    def test_else(self):
        res = resolve("""
            foo:
                bar: 42
                wibble: 22
            bar: {{ foo.baz or foo.bar }}
            baz: {{ foo.baz or foo.qux or foo.bar }}
            qux: {{ foo.wibble or foo.baz }}
            """)
        self.assertEqual(res['bar'], 42)
        self.assertEqual(res['baz'], 42)
        self.assertEqual(res['qux'], 22)

    def test_else_empty_list(self):
        res = resolve("""
            foo: {{ a or [] }}
            """)
        self.assertEqual(res['foo'], [])

    def test_else_empty_dict(self):
        res = resolve("""
            foo: {{ a or {} }}
            """)
        self.assertEqual(res['foo'], {})

    def test_else_string(self):
        res = resolve("""
            foo: {{ a or "foo" }}
            """)
        self.assertEqual(res['foo'], "foo")

    def test_else_include(self):
        res = resolve("""
            include (a or "foo") + "_inc"
            """,
            foo_inc="hello:world\n")
        self.assertEqual(res['hello'], 'world')


class TestNot(unittest2.TestCase):
    def test_not_true(self):
        t = parse("""
            foo: {{ not 0 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 1)

    def test_not_false(self):
        t = parse("""
            foo: {{ not 1 }}
            """)
        self.assertEqual(t.get("foo").as_int(), 0)


class TestConditionalExpression(unittest2.TestCase):

    def test_eval_true(self):
        t = parse("""
            foo: {{ "foo" if 1 else "bar" }}
            """)
        self.assertEqual(t.get("foo").resolve(), "foo")

    def test_eval_false(self):
        t = parse("""
            foo: {{ "foo" if 0 else "bar" }}
            """)
        self.assertEqual(t.get("foo").resolve(), "bar")


class TestListDisplay(unittest2.TestCase):

    def test_empty(self):
        t = parse("""
          foo: {{ [] }}
          """)
        self.assertEqual(t.get("foo").resolve(), [])

    def test_list_comprehension(self):
        res = resolve("""
            foo: {{ [a+1 for a in range(5)] }}
            """)
        self.assertEqual(res['foo'], [1, 2, 3, 4, 5])


class TestDictDisplay(unittest2.TestCase):

    def test_empty(self):
        t = parse("""
            foo: {{ {} }}
            """)
        self.assertEqual(t.get("foo").resolve(), {})


class TestAttributeRef(unittest2.TestCase):

    def test_attributeref(self):
        res = resolve("""
            a:
              b: hello
            bar: {{ a.b }}
            """)
        self.assertEqual(res['bar'], 'hello')


class TestSubscription(unittest2.TestCase):

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
        self.assertEqual(t.get("bar").as_int(), 2)

    def test_subscription_of_list_with_identifier(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            qux: 0

            bar: {{ foo[qux] }}
            """)
        self.assertEqual(t.get("bar").as_int(), 1)

    def test_subscription_of_list_nested(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            bar: {{ foo[foo[0]] }}
            """)
        self.assertEqual(t.get("bar").as_int(), 2)


class TestFor(unittest2.TestCase):

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
        self.assertEqual(res['baz'], [{'nameage': 'john28', 'agename': '28john'}])

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
        self.assertEqual(res['bar'], [1,2,3])
        self.assertEqual(res['baz'], [1,2,3])

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

    @unittest2.expectedFailure
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

                select i
                    0:
                      - {{ i }}

            """)
        self.assertEqual(res["wibble"], [0, 2, 3])

class TestSlicing(unittest2.TestCase):

    def test_simple_slicing(self):
        t = parse("""
            foo:
              - 1
              - 2
              - 3

            bar: {{ foo[0:2] }}
            """)
        self.assertEqual(t.get("bar").resolve(), [1, 2])

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

        self.assertEqual(res['listb'], [1,2])
        self.assertEqual(res['listc'], [1,2])
        self.assertEqual(res['listd'], [1,2])

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

        self.assertEqual(res['listb'], [1,3,5])


class TestPythonCall(unittest2.TestCase):

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
        self.assertEqual(res['b'], [0,-1,-2,-3,-4])

    def test_replace(self):
        res = resolve("""
            teststring: foo bar baz
            replacedstring: {{ replace(teststring, " ", "-") }}
            """)
        self.assertEqual(res['replacedstring'], 'foo-bar-baz')


class TestMacroCall(unittest2.TestCase):

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

class TestExtend(unittest2.TestCase):

    def test_simple_extend(self):
        t = parse("""
            foo:
              - 1
              - 2

            extend foo:
              - 1
            """)
        self.assertEqual(t.get("foo").resolve(), [1, 2, 1])

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

    def test_extend_list_with_variable(self):
        res = resolve("""
            someval: julian
            somelist: []
            extend somelist:
              - {{ someval }}
            """)
        self.assertEqual(res['somelist'], ['julian'])


class TestInclude(unittest2.TestCase):

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
        self.assertEqual(res, {"resources": [1,2,3]})

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
        self.assertEqual(res, {"wibble": "wobble", "hello": "world", "foo": "bar"})

    def test_magic_1(self):
        res = resolve("""
            include foo
            include "magic_1_1"
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


class TestSelect(unittest2.TestCase):

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


class TestIf(unittest2.TestCase):

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


class TestYayScalar(unittest2.TestCase):

    def test_int(self):
        res = resolve("""
            foo: 1
            """)
        self.assertEqual(res['foo'], 1)

    def test_int_type_error(self):
        t = parse("""
            foo: bar
            """)
        self.assertRaises(errors.TypeError, t.get('foo').as_int)


class TestSet(unittest2.TestCase):
    pass

    #def test_set(self):
    #    res = resolve("""
    #        set foo = "Simple expression"
    #        set bar = foo
    #        quux: {{ bar }}
    #        """)
    #    self.assertEqual(res, {"quux": "bar"})


class TestOpeners(unittest2.TestCase):
    pass

    #def test_openers_package_compat(self):
        #res = resolve("""
            #% include "package://yay.tests/fixtures/hello_world.yay"
            #""")
        #self.assertEqual(res['hello'], 'world')

    #def test_openers_search(self):
        #res = resolve("""
            #% search "package://yay/tests/fixtures"
            #% include "somefile.yay"
            #% include "onlyin2.yay"
            #""")

        ## FIXME: Need to figure out how search interacts with the MockRoot searchpath..
        #self.assertEqual(True, False)

    #def test_openers_config(self):
        #res = resolve("""
            #configure openers:
                #packages:
                    #index: http://b.pypi.python.org/simple
                #memory:
                    #example:
                        #hello: world

            #% include 'mem://example'
            #""")

        #self.assertEqual(res['hello'], 'world')

