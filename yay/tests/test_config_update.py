import unittest
from yay.config import Config
from yay.ordereddict import OrderedDict

class TestConfigUpdate(unittest.TestCase):

    def test_simple_update(self):
        c = Config()
        c.update(OrderedDict(foo=1, bar=2, baz=3))

        self.failUnless('foo' in c._raw.keys())

    def test_simple_replace(self):
        c = Config()
        c.update(OrderedDict(foo=1, bar=2, baz=3))
        c.update(OrderedDict(foo=3, qux=1))

        self.failUnlessEqual(c._raw['foo'], 3)
        self.failUnlessEqual(c._raw['bar'], 2)
        self.failUnlessEqual(c._raw['qux'], 1)

    def test_nested_map_update(self):
        c = Config()
        c.update(OrderedDict(foo=OrderedDict(foo=1, bar=2), bar=2))
        c.update(OrderedDict(foo=OrderedDict(foo=2, baz=3), baz=3))

        self.failUnlessEqual(c._raw['foo']['foo'], 2)
        self.failUnlessEqual(c._raw['foo']['bar'], 2)
        self.failUnlessEqual(c._raw['foo']['baz'], 3)
        self.failUnlessEqual(c._raw['baz'], 3)
