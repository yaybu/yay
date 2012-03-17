from unittest import TestCase
from yay.errors import Error
import yay

class TestFails(TestCase):

    def test_append_mapping_to_list(self):
        yaystr = """
        foo:
          - 1

        foo.append:
          blarg: hello
        """

        self.failUnlessRaises(Error, yay.load, yaystr)

    def test_append_list_to_mapping(self):
        yaystr = """
        foo: hello
        foo.append:
          - 1
        """

        self.failUnlessRaises(Error, yay.load, yaystr)

