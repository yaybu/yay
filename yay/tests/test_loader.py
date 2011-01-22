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
