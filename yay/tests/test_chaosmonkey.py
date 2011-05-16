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
import os
import random

from yay.config import Config
from yay.openers import MemOpener
from yay.errors import Error


class TestChaosMonkey(unittest.TestCase):

    def test_chaos(self):
        path = os.path.dirname(__file__)
        raw = open(os.path.join(path, "test_chaosmonkey.yay")).read()

        for i in range(1000):
            idx = random.randint(0, len(raw)-1)
            ln = random.randint(1, 100)

            action = random.choice(["delete", "add"])

            if action == "delete":
                copy = self.delete(raw, idx, ln)
            elif action == "add":
                copy = self.add(raw, idx, ln)

            try:
                MemOpener.add("mem://test_chaosmonkey", copy)
                Config().load_uri("mem://test_chaosmonkey")
            except Error, e:
                pass
            except Exception, e:
                print type(e), idx, len, action
                raise

    def add(self, raw, idx, len):
        return raw[:idx] + " " * len + raw[idx:]

    def delete(self, raw, idx, len):
        return raw[:idx] + raw[idx+len:]

