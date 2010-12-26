import unittest
from yay.config import Config
from yay.ordereddict import OrderedDict

class TestConfigUpdate(unittest.TestCase):

    def test_simple_update(self):
        c = Config()

        o = OrderedDict()
        o['foo'] = '1'
        o['bar'] = '2'
        o['baz'] = '3'

        c.update(o)

        self.failUnless('foo' in c._raw.keys())
