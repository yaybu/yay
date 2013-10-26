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

from yay.ast import If, Literal
from yay.tests.test_ast_common import DynamicLiteral, ComplexLiteral
from yay.tests.base import TestCase

import mock

"""
class TestIfDymnamic(TestCase):

    def test_if_dynamic_guard_true(self):
        n = If(Literal(True), Literal("dog"), else_=Literal("cat"))
        self.assertEqual(n.dynamic(), False)

    def test_if_dynamic_guard_false(self):
        n = If(Literal(False), Literal("dog"), else_=Literal("cat"))
        self.assertEqual(n.dynamic(), False)

    def test_dynamicguard(self):
        n = If(DynamicLiteral(True), Literal("dog"), else_=Literal("cat"))
        self.assertEqual(n.dynamic(), True)


class TestIfSimplification(TestCase):

    def test_if_simplify_guard_true(self):
        n = If(Literal(True), ComplexLiteral("dog"), else_=Literal("cat"))
        res = n.simplify()

        self.assertTrue(not isinstance(res, ComplexLiteral))
        self.assertEqual(res.literal, "dog")

    def test_if_simplify_guard_false(self):
        n = If(Literal(False), Literal("dog"), else_=ComplexLiteral("cat"))
        res = n.simplify()

        self.assertTrue(not isinstance(res, ComplexLiteral))
        self.assertEqual(res.literal, "cat")

    def test_if_dynamicguard(self):
        n = If(DynamicLiteral(False), Literal("dog"), else_=Literal("cat"))
        res = n.simplify()

        # We can't simplify the containing expression away as the guard
        # is dynamic.
        self.assertNotEqual(n, res)
        self.assertTrue(isinstance(res, If))
        self.assertEqual(res.condition.literal, False)

        # However we can simplify the true/false result
        # In this case ComplexLiteral's should simplify away.
        self.assertTrue(not isinstance(res.result.literal, ComplexLiteral))
        self.assertEqual(res.result.literal, "dog")
        self.assertTrue(not isinstance(res.else_.literal, ComplexLiteral))
        self.assertEqual(res.else_.literal, "cat")
"""


class TestIfResolve(TestCase):

    def test_if_resolve_true(self):
        n = If(Literal(True), Literal("dog"), Literal("cat"))
        n.anchor = mock.Mock()
        self.assertEqual(n.resolve(), "dog")

    def test_if_resolve_false(self):
        n = If(Literal(False), Literal("dog"), Literal("cat"))
        n.anchor = mock.Mock()
        self.assertEqual(n.resolve(), "cat")
