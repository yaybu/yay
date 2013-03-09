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

import unittest
from yay.ast import Expr, Literal
from yay.tests.test_ast_common import DynamicLiteral, ComplexLiteral


class TestEqSimplification(unittest.TestCase):

    def test_both_dynamic(self):
        n = Expr(DynamicLiteral('left'), DynamicLiteral('right'), '==')
        res = n.simplify()

        self.assertTrue(isinstance(res, Expr))
        self.assertEqual(res.lhs.literal, 'left')
        self.assertEqual(res.rhs.literal, 'right')

    def test_left_dynamic(self):
        n = Expr(DynamicLiteral('left'), ComplexLiteral('right'), '==')
        res = n.simplify()

        # Unable to simplify Expr because left side not constant
        self.assertTrue(isinstance(res, Expr))
        # Left side not simplified because its dynamic
        self.assertEqual(res.lhs.literal, 'left')
        self.assertTrue(isinstance(res.lhs, DynamicLiteral))
        # Right side simplified from ComplexLiteral
        self.assertEqual(res.rhs.literal, 'right')
        self.assertTrue(not isinstance(res.rhs, ComplexLiteral))

    def test_right_dynamic(self):
        n = Expr(ComplexLiteral('left'), DynamicLiteral('right'), '==')
        res = n.simplify()

        # Unable to simplify Expr because right side not constant
        self.assertTrue(isinstance(res, Expr))
        # Left side simplified from ComplexLiteral
        self.assertEqual(res.lhs.literal, 'left')
        self.assertTrue(not isinstance(res.lhs, ComplexLiteral))
        # Right side not simplified because its dynamic
        self.assertEqual(res.rhs.literal, 'right')
        self.assertTrue(isinstance(res.rhs, DynamicLiteral))

    def test_neither_dynamic(self):
        n = Expr(ComplexLiteral('left'), ComplexLiteral('right'), '==')
        res = n.simplify()

        # Both sides constant so expression simplified to a literal
        self.assertTrue(isinstance(res, Literal))
        self.assertEqual(res.literal, False)


class TestEqResolve(unittest.TestCase):

    def test_cond_true(self):
        n = Expr(Literal(4), Literal(4), '==')
        self.assertEqual(n.resolve(), True)

    def test_cond_false(self):
        n = Expr(Literal(4), Literal(5), '==')
        self.assertEqual(n.resolve(), False)
