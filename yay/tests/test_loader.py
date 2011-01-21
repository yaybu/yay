import unittest
import yaml
from yay.loader import Loader
from yay.ordereddict import OrderedDict

test_str = """
foo:
    bar: 1
    bar.append: 2
"""


class TestLoader(unittest.TestCase):

    def test_loader(self):
        foo = yaml.load(test_str, Loader=Loader)
        self.failUnless(isinstance(foo, OrderedDict))
