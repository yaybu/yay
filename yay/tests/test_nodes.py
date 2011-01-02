import unittest
from yay.config import *

class TestListOperations(unittest.TestCase):

    def test_list(self):
        l = List([Boxed(1), Boxed(2), Boxed(3)])

        self.failUnlessEqual(l.resolve(), [1, 2, 3])

    def test_list_append(self):
        l = List([Boxed(1), Boxed(2), Boxed(3)])
        a = Append(List([Boxed(4), Boxed(5)]))
        a.chain = l

        self.failUnlessEqual(a.resolve(), [1,2,3,4,5])

    def test_list_remove(self):
        l = List([Boxed(1), Boxed(2), Boxed(3)])
        r = Remove(List([Boxed(2)]))
        r.chain = l

        self.failUnlessEqual(r.resolve(), [1, 3])

class TestLookup(unittest.TestCase):

    def test_lookup(self):
        d = Dictionary(None)
        d.set("foo", Boxed(1))
        l = Lookup(d, Boxed("foo"))
 
        self.failUnlessEqual(l.resolve(), 1)
