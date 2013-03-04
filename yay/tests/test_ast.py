import unittest
from yay.ast import *
from mock import Mock


class TestAST(unittest.TestCase):

    def test_dynamic(self):
        self.assertEqual(AST().dynamic(), False)

    def test_clone_preserve_class(self):
        class ExampleNode(AST):
            pass
        e1 = ExampleNode()
        self.assertNotEqual(e1, e1.clone())
        self.assertTrue(isinstance(e1.clone(), ExampleNode))

    def test_clone_attr_ast(self):
        e1 = AST()
        e1.somevalue = AST()
        e1.somevalue.text = "hello"
        clone = e1.clone()

        self.assertEqual(clone.somevalue.text, "hello")
        self.assertNotEqual(clone.somevalue, e1.somevalue)
        self.assertNotEqual(clone, e1)

    def test_clone_list_of_ast(self):
        e1, e2, e3 = AST(), AST(), AST()
        e2.value = "e2"
        e3.value = "e3"
        e1.values = [e2, e3]
        clone = e1.clone()

        self.assertEqual(clone.values[0].value, "e2")
        self.assertEqual(clone.values[1].value, "e3")
        self.assertNotEqual(clone, e1)
        self.assertNotEqual(clone.values[0], e2)
        self.assertNotEqual(clone.values[1], e3)

    def test_clone_dict_of_ast(self):
        e1, e2, e3 = AST(), AST(), AST()
        e2.value = "e2"
        e3.value = "e3"
        e1.values = {"e2":e2, "e3":e3}
        clone = e1.clone()

        self.assertEqual(clone.values['e2'].value, "e2")
        self.assertEqual(clone.values['e3'].value, "e3")
        self.assertNotEqual(clone, e1)
        self.assertNotEqual(clone.values['e2'], e2)
        self.assertNotEqual(clone.values['e3'], e3)

    def test_equality(self):
        e1, e2 = AST(), AST()
        e1.value = "hello"
        e2.value = "hello"
        self.assertEqual(e1, e2)
        e2.value = "goodbye"
        self.assertNotEqual(e1, e2)

class TestRoot(unittest.TestCase):

    def test_get_root(self):
        root = Root(Mock())
        self.assertEqual(root.get_root(), root)

    def test_get_context(self):
        root = Root(Mock())
        root.get_context('hello')
        root.node.get.assert_called_with('hello')

    def test_get_context_no_matching(self):
        # FIXME
        pass

    def test_resolve(self):
        root = Root(Mock())
        root.resolve()
        root.node.resolve.assert_called_with()

class TestIdentifier(unittest.TestCase):

    def test_resolve(self):
        identifier = Identifier("global_var")
        identifier.parent = Mock()
        identifier.resolve()
        identifier.parent.get_context.assert_called_with("global_var")

class TestLiteral(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(Literal("hello").resolve(), "hello")

class TestPower(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(Power(Literal(2), Literal(2)).resolve(), 4)

class TestUnary(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(UnaryMinus(Literal(2)).resolve(), -2)

class TestInvert(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(Invert(Literal(2)).resolve(), ~2)

class TestNot(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(Not(Literal(False)).resolve(), True)

class TestConditionalExpression(unittest.TestCase):

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

class TestYayList(unittest.TestCase):
    def test_resolve(self):
        y = YayList(Literal(1), Literal(2), Literal(3))
        self.assertEqual(y.resolve(), [1,2,3])

class TestYayDict(unittest.TestCase):
    def test_resolve(self):
        y = YayDict([("a", Literal(1))])
        self.assertEqual(y.resolve(), {"a": 1})

    def test_get(self):
        #FIXME:
        pass

    def test_update(self):
        #FIXME
        pass

