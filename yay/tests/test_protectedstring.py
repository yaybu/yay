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
from yay import String


class TestString(unittest.TestCase):

    def test_normal_string(self):
        a = String(["Just a normal string"])

        self.failUnlessEqual(unicode(a), "Just a normal string")
        self.failUnlessEqual(a.unprotected, "Just a normal string")

        self.failUnlessEqual(a.as_list(secret=True), ["Just a normal string"])
        self.failUnlessEqual(a.as_list(secret=False), ["Just a normal string"])

    def test_partially_secret(self):
        a = "adduser -u fred -p "
        b = String()
        b.add_secret("password")
        c = " -h /home/fred"
        d = String([a,b,c])

        self.failUnlessEqual(unicode(d), "adduser -u fred -p ***** -h /home/fred")
        self.failUnlessEqual(d.unprotected, "adduser -u fred -p password -h /home/fred")

        self.failUnlessEqual(d.as_list(secret=True), ["adduser -u fred -p ", "*****", " -h /home/fred"])
        self.failUnlessEqual(d.as_list(secret=False), ["adduser -u fred -p ", "password", " -h /home/fred"])

