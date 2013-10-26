# Copyright 2010-2013 Isotoma Limited
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


from yay.openers import *
from yay.errors import NotModified, NotFound, ParadoxError
from yay.tests.base import TestCase

if __file__.endswith(".pyc"):
    __file__ = __file__[:-1]


class TestFileOpener(TestCase):

    def test_read(self):
        fp = FileOpener().open(__file__)
        data = fp.read().decode("utf-8").splitlines()
        self.failUnlessEqual(data[0], "# Copyright 2010-2013 Isotoma Limited")

    def test_notfound(self):
        fo = FileOpener()
        self.failUnlessRaises(NotFound, fo.open, __file__ + ".zzzzzzzzzz")

    def test_etag(self):
        fo = FileOpener()
        fp = fo.open(__file__)
        etag = fp.etag
        fp.close()

        self.failUnlessRaises(NotModified, fo.open, __file__, etag)

    def test_len(self):
        fp = FileOpener().open(__file__)
        self.failUnlessEqual(len(fp.read()), fp.len)


class TestHttpOpener(TestCase):
    pass
    # def test_notfound(self):
    #    uo = UrlOpener()
    #    self.failUnlessRaises(NotFound, uo.open, "http://yay-test-url-that-doesnt-exist.isotoma.com/hello_world")


class TestLazySearchpath(TestCase):

    def setUpMock(self, iterable):
        class Mock(object):

            def __init__(self, foo):
                self.foo = foo

            def as_iterable(self):
                for f in self.foo:
                    yield f

        self.mock = Mock(iterable)
        self.searchpath = SearchpathFromGraph(self.mock)

    def test_simple(self):
        self.setUpMock(["/tmp"])
        self.assertEqual(list(self.searchpath), ["/tmp"])

    def test_simple_and_repeatable(self):
        self.setUpMock(["/tmp"])
        self.assertEqual(list(self.searchpath), ["/tmp"])
        self.assertEqual(list(self.searchpath), ["/tmp"])

    def test_can_grow(self):
        self.setUpMock(["/tmp"])
        self.assertEqual(list(self.searchpath), ["/tmp"])
        self.mock.foo.append("/dev/null")
        self.assertEqual(list(self.searchpath), ["/tmp", "/dev/null"])

    def test_cant_shrink(self):
        self.setUpMock(["/tmp", "/dev/null"])
        list(self.searchpath)
             # only a causality problem if its been accessed already
        self.mock.foo.remove("/dev/null")
        self.assertRaises(ParadoxError, list, self.searchpath)

    def test_cant_change(self):
        self.setUpMock(["/tmp", "/dev/null"])
        list(self.searchpath)
             # only a causality problem if its been accessed already
        self.mock.foo = ["/dev/null", "/tmp"]
        self.assertRaises(ParadoxError, list, self.searchpath)
