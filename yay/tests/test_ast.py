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

from yay.ast import *
from yay.tests.base import TestCase
from mock import Mock


class TestAST(TestCase):

    def test_dynamic(self):
        self.assertEqual(AST().dynamic(), False)

    def test_clone_preserve_class(self):
        class ExampleNode(AST):
            pass
        e1 = ExampleNode()
        self.assertNotEqual(id(e1), id(e1.clone()))
        self.assertTrue(isinstance(e1.clone(), ExampleNode))

    def test_clone_attr_ast(self):
        e1 = AST()
        e1.somevalue = AST()
        e1.somevalue.text = "hello"
        clone = e1.clone()

        self.assertEqual(clone.somevalue.text, "hello")
        self.assertNotEqual(id(clone.somevalue), id(e1.somevalue))
        self.assertNotEqual(id(clone), id(e1))

    def test_clone_list_of_ast(self):
        e1, e2, e3 = AST(), AST(), AST()
        e2.value = "e2"
        e3.value = "e3"
        e1.values = [e2, e3]
        clone = e1.clone()

        self.assertEqual(clone.values[0].value, "e2")
        self.assertEqual(clone.values[1].value, "e3")
        self.assertNotEqual(id(clone), id(e1))
        self.assertNotEqual(id(clone.values[0]), id(e2))
        self.assertNotEqual(id(clone.values[1]), id(e3))

    def test_clone_dict_of_ast(self):
        e1, e2, e3 = AST(), AST(), AST()
        e2.value = "e2"
        e3.value = "e3"
        e1.values = {"e2":e2, "e3":e3}
        clone = e1.clone()

        self.assertEqual(clone.values['e2'].value, "e2")
        self.assertEqual(clone.values['e3'].value, "e3")
        self.assertNotEqual(id(clone), id(e1))
        self.assertNotEqual(id(clone.values['e2']), id(e2))
        self.assertNotEqual(id(clone.values['e3']), id(e3))

    def test_equality(self):
        e1, e2 = AST(), AST()
        e1.value = "hello"
        e2.value = "hello"
        self.assertEqual(e1, e2)
        e2.value = "goodbye"
        self.assertNotEqual(id(e1), id(e2))


class TestRoot(TestCase):

    def test_get_root(self):
        root = Root(Mock())
        self.assertEqual(root.root, root)

    def test_get_context_no_matching(self):
        # FIXME
        pass

    def test_resolve(self):
        inner = Mock()
        inner.expand.side_effect = lambda: inner

        root = Root(inner)
        root.resolve()
        inner.resolve.assert_called_with()

class TestIdentifier(TestCase):

    def test_resolve(self):
        identifier = Identifier("global_var")
        identifier.parent = Mock()
        identifier.resolve()
        identifier.parent.get_context.assert_called_with("global_var")

class TestLiteral(TestCase):
    def test_resolve(self):
        self.assertEqual(Literal("hello").resolve(), "hello")

class TestPower(TestCase):
    def test_resolve(self):
        self.assertEqual(Power(Literal(2), Literal(2)).resolve(), 4)

class TestUnary(TestCase):
    def test_resolve(self):
        self.assertEqual(UnaryMinus(Literal(2)).resolve(), -2)

class TestInvert(TestCase):
    def test_resolve(self):
        self.assertEqual(Invert(Literal(2)).resolve(), ~2)

class TestNot(TestCase):
    def test_resolve(self):
        self.assertEqual(Not(Literal(False)).resolve(), True)

class TestConditionalExpression(TestCase):

    def test_resolve_if(self):
        self.assertEqual(
            ConditionalExpression(Literal(True), Literal("IF"), Literal("ELSE")).resolve(),
            "IF"
            )

    def test_resolve_else(self):
        self.assertEqual(
            ConditionalExpression(Literal(False), Literal("IF"), Literal("ELSE")).resolve(),
            "ELSE"
            )

class TestYayList(TestCase):
    def test_resolve(self):
        y = YayList(Literal(1), Literal(2), Literal(3))
        self.assertEqual(y.resolve(), [1,2,3])

class TestYayDict(TestCase):
    def test_resolve(self):
        y = YayDict([("a", Literal(1))])
        y.anchor = Mock()
        self.assertEqual(y.resolve(), {"a": 1})

    def test_get(self):
        #FIXME:
        pass

    def test_update(self):
        #FIXME
        pass

class TestYayExtend(TestCase):
    def test_resolve(self):
        y = YayExtend(YayList(Literal(1)))
        y.anchor = None
        y.predecessor = YayList(Literal(2))
        y.parent = Mock()
        self.assertEqual(y.resolve(), [2, 1])

class TestFor(TestCase):
    def test_resolve(self):
        f = For(Identifier("x"), YayList(Literal('a'), Literal('b')), YayList(Identifier("x")))
        f.parent = Mock()
        f.anchor = Mock()
        self.assertEqual(f.resolve(), ['a', 'b'])

    def test_resolve_filtered(self):
        f = For(Identifier("x"), YayList(Literal('a'), Literal('b')), YayList(Identifier("x")), Equal(Identifier("x"), Literal("a")))
        f.parent = Mock()
        f.anchor = Mock()
        self.assertEqual(f.resolve(), ['a'])

class TestContext(TestCase):

    def test_get_context_hit(self):
        c = Context(Mock(), {"x": Mock()})
        x = c.get_context("x")
        self.assertEqual(x, c.context["x"])
