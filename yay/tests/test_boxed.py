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
from yay.nodes.boxed import Boxed


class TestResolver(unittest.TestCase):
    pass


class Old:
    def test_string(self):
        r = Resolver({
            "foo": "123",
            "baz": "{foo}",
            }).resolve()

        self.failUnlessEqual(r["baz"], "123")

    def test_list(self):
        r = Resolver({
            "foo": "123",
            "baz": [
                "456",
                "{foo}",
                ],
            }).resolve()

        self.failUnlessEqual(r['baz'], ["456", "123"])

    def test_nested_dict(self):
        r = Resolver({
            "foo": 123,
            "baz": {
                "foo": "{foo}",
                },
            }).resolve()

        self.failUnlessEqual(r['baz']['foo'], "123")

    def test_cycle_detection(self):
        r = Resolver({
            "foo": "{baz}",
            "baz": "{foo}",
            })

        self.failUnlessRaises(ValueError, r.resolve)

