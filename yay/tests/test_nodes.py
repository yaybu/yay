import unittest
from yay.nodes import *
from yay.context import Context

class TestSequenceOperations(unittest.TestCase):

    def setUp(self):
        self.ctx = Context(None, None)

    def test_Sequence(self):
        l = Sequence([Boxed(1), Boxed(2), Boxed(3)])

        self.failUnlessEqual(l.resolve(self.ctx), [1, 2, 3])

    def test_Sequence_append(self):
        l = Sequence([Boxed(1), Boxed(2), Boxed(3)])
        a = Append(Sequence([Boxed(4), Boxed(5)]))
        a.chain = l

        self.failUnlessEqual(a.resolve(self.ctx), [1,2,3,4,5])

    def test_Sequence_remove(self):
        l = Sequence([Boxed(1), Boxed(2), Boxed(3)])
        r = Remove(Sequence([Boxed(2)]))
        r.chain = l

        self.failUnlessEqual(r.resolve(self.ctx), [1, 3])


class TestMapping(unittest.TestCase):

    def setUp(self):
        self.ctx = Context(None, None)

    def test_get_set(self):
        d = Mapping(None)
        d.set("foo", Boxed(1))

        self.failUnlessEqual(d.get(None, "foo", None).value, 1)


class TestLookup(unittest.TestCase):

    def setUp(self):
        self.ctx = Context(None, None)

    def test_lookup(self):
        d = Mapping(None)
        d.set("foo", Boxed(1))
        l = Lookup(d, Boxed("foo"))
 
        self.failUnlessEqual(l.resolve(self.ctx), 1)

