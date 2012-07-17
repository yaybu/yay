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
from yay.openers import *
from yay.errors import NotModified, NotFound


if __file__.endswith(".pyc"):
    __file__ = __file__[:-1]


class TestFileOpener(unittest.TestCase):

    def test_read(self):
        fp = FileOpener().open(__file__)
        data = fp.read().split("\n")
        self.failUnlessEqual(data[0], "# Copyright 2010-2011 Isotoma Limited")

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


class TestHttpOpener(unittest.TestCase):

    def test_notfound(self):
        uo = UrlOpener()
        self.failUnlessRaises(NotFound, uo.open, "http://yay-test-url-that-doesnt-exist.isotoma.com/hello_world")


class TestMemOpener(unittest.TestCase):

    def test_read(self):
        MemOpener.data['hello'] = "test data"
        self.failUnlessEqual("test data", MemOpener().open("mem://hello").read())

    def test_notfound(self):
        self.failUnlessRaises(NotFound, MemOpener().open, "mem://does-not-exist")

    def test_etag(self):
        MemOpener.data['hello'] = "test data"
        mo = MemOpener()
        fp = mo.open("mem://hello")
        etag = fp.etag
        fp.close()

        self.failUnlessRaises(NotModified, mo.open, "mem://hello", etag)


