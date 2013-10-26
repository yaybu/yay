# Copyright 2013 Isotoma Limited
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

from yay import config
from yay.compat import io
from yay.errors import ProgrammingError, NoMatching
from yay.tests.base import TestCase


class TestConfig(TestCase):

    def test_create_empty(self):
        c = config.Config()
        self.assertEqual(c.resolve(), {})

    def test_create_and_add(self):
        c = config.Config()
        c.add(dict(
            foo=1,
        ))
        self.assertEqual(c.resolve(), {"foo": 1})

    def test_create_and_add_exception(self):
        c = config.Config()
        self.assertRaises(ProgrammingError, c.add, "foo bar")

    def test_get_context_miss(self):
        c = config.Config()
        c.add(dict(
            foo=1,
        ))
        self.assertRaises(NoMatching, c.get_context, "foo bar")

    def test_get_context_miss_empty(self):
        c = config.Config()
        self.assertRaises(NoMatching, c.get_context, "foo bar")

    def test_load_and_resolve_stream(self):
        resolved = config.load(io.StringIO("""
            hello: world
            """))
        self.assertEqual(resolved, {"hello": "world"})

    def test_load_and_resolve_fp(self):
        resolved = config.load_uri(self._config("""
            hello: world
            """))
        self.assertEqual(resolved, {"hello": "world"})
