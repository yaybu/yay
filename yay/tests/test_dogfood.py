# Copyright 2011 Isotoma Limited
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
import doctest
import os
import glob

import yaml

from yay.config import Config
from yay.openers import MemOpener

dogfood_path = os.path.join(os.path.dirname(__file__), "dogfood")


class TestConfig(Config):

    def load_uri(self, uri):
        return super(TestConfig, self).load_uri("file:///" + os.path.join(dogfood_path, uri))


class TestDogfood(unittest.TestCase):

    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            # Generate a testcase for each .in file in the dogfood directory
            for snack in list(os.path.splitext(os.path.basename(x))[0] for x in glob.glob(os.path.join(dogfood_path, "*.in"))):
                name, func = cls.get_test_method(snack)
                attrs[name] = func
            return type.__new__(cls, name, bases, attrs)

        @classmethod
        def get_test_method(cls, snack):
            name = "test_%s" % snack
            load_from = os.path.join(dogfood_path, snack+".in")
            compare_to = os.path.join(dogfood_path, snack+".out")
            def _(self):
               self.failUnlessEqual(self.load(load_from), yaml.load(open(compare_to)))
            _.__name__ = name
            return name, _

    def load(self, path):
        oldpath = os.getcwd()
        os.chdir(dogfood_path)
        try:
            c = TestConfig()
            self.failUnlessEqual(c.get(), {})
            c.load_uri(path)
            return c.get()
        finally:
            os.chdir(oldpath)

    def failUnlessEqual(self, value1, value2):
        if not isinstance(value1, dict) or not isinstance(value2, dict):
            super(TestDogfood, self).failUnlessEqual(value1, value2)
            return

        k1 = frozenset(value1.keys())
        k2 = frozenset(value2.keys())

        if k1.difference(k2):
            raise KeyError("Dictionary 1 contains keys dictionary 2 does not (%s)" % ", ".join(k1.difference(k2)))

        if k2.difference(k1):
            raise KeyError("Dictionary 2 contains keys dictionary 1 does not (%s)" % ", ".join(k2.difference(k1)))

        for key in k1:
            self.failUnlessEqual(value1[key], value2[key])

