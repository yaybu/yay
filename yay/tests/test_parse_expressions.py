# Copyright 2011 Isotoma Limited
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
from yay.parser import templated_string

class TestTemplatedString(unittest.TestCase):

    def do(self, teststring, expect):
        self.failUnlessEqual(
            repr(templated_string.parseString(teststring)[0]),
            expect
            )

    def test_template_whole_string(self):
        self.do("{foo}", "Access(None, foo)")

    def test_template_middle_of_string(self):
        self.do("foo{bar}baz", "Concat(Boxed(foo), Access(None, bar), Boxed(baz))")

    def test_template_middle_of_string_with_spaces(self):
        self.do("foo {bar} baz", "Concat(Boxed(foo ), Access(None, bar), Boxed( baz))")

    def test_template_start_of_string(self):
        self.do("{foo} bar", "Concat(Access(None, foo), Boxed( bar))")

    def test_template_end_of_string(self):
        self.do("foo {bar}", "Concat(Boxed(foo ), Access(None, bar))")

