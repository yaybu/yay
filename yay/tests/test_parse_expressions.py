
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

