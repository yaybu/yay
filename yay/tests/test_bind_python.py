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
import yay
from yay.config import Config

from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


test_yay = """
injected_data: abc

result: ${injected_data}
"""


class TestInjectPython(unittest.TestCase):

    def test_override_literal(self):
        config = Config()
        config.load(test_yay)
        config.add(dict(injected_data="xyz"))

        self.failUnlessEqual(config.get()["result"], "xyz")

