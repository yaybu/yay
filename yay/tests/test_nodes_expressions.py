# Copyright 2010-2011 Isotoma Limited
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
from yay.nodes import *

class TestNodeExpressions(unittest.TestCase):

    def test_and(self):
        for a in (True, False):
            for b in (True, False):
                c = And(Boxed(a), Boxed(b))
                self.failUnlessEqual(c.resolve(), a and b)

    def test_or(self):
        for a in (True, False):
            for b in (True, False):
                c = Or(Boxed(a), Boxed(b))
                self.failUnlessEqual(c.resolve(), a or b)

    def test_in(self):
        b = ["a", "b", "c", "d"]
        
        c = In(Boxed("a"), Boxed(b))
        self.failUnless(c.resolve())

        c = In(Boxed("z"), Boxed(b))
        self.failUnless(not c.resolve())

    def test_equals(self):
        a = Boxed(5)
        b = Boxed(5)
        c = Equal(a, b)
        self.failUnless(c.resolve())

    def test_not_equals(self):
        a = Boxed(5)
        b = Boxed(4)
        c = NotEqual(a, b)
        self.failUnless(c.resolve())

    def test_lt(self):
        a = Boxed(3)
        b = Boxed(4)
        c = LessThan(a, b)
        self.failUnless(c.resolve())

    def test_lte(self):
        a = Boxed(3)
        b = Boxed(4)
        c = LessThanEqual(a, b)
        self.failUnless(c.resolve())

    def test_gt(self):
        a = Boxed(5)
        b = Boxed(4)
        c = GreaterThan(a, b)
        self.failUnless(c.resolve())

    def test_gte(self):
        a = Boxed(5)
        b = Boxed(4)
        c = GreaterThanEqual(a, b)
        self.failUnless(c.resolve())

    def test_function(self):
        r = Function("sum", [Boxed(5), Boxed(5)])
        self.failUnlessEqual(r.resolve(), 10)

