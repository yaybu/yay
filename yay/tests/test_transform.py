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

from yay.transform import main
from yay.compat import io
from yay.errors import ProgrammingError, NoMatching
from yay.tests.base import TestCase


class TestTransform(TestCase):

    def setUp(self):
        self.stream = io.StringIO("""
            hello: world
            foo:
                bar: 1
                baz: {{ hello }}
            qux:
              - 1
              - 2
            """)

    def test_trigger_usage(self):
        self.assertRaises(SystemExit, main, argv=["a", "b", "c"])

    def test_format_validation(self):
        self.assertRaises(
            SystemExit, main, argv=["-f", "pyx"], stdin=self.stream)

    def test_phase_validation(self):
        self.assertRaises(
            SystemExit, main, argv=["-p", "pyx"], stdin=self.stream)

    def test_successful_py(self):
        main(argv=["-f", "py"], stdin=self.stream)

    def test_successful_yaml(self):
        main(argv=["-f", "yaml"], stdin=self.stream)

    def test_successful_dot(self):
        main(argv=["-f", "dot"], stdin=self.stream)

    # def test_successful_dot_with_phase(self):
    #    main(argv=["-f", "dot", "-p", "normalized"], stdin=self.stream)


class TestTransformParseErrors(TestCase):

    def setUp(self):
        self.stream = io.StringIO("""
            hello: world
            foo:
                bar: 1
                baz: {{ hello
            qux:
              - 1
              - 2
            """)

    def test_py(self):
        self.assertRaises(
            SystemExit, main, argv=["-f", "py"], stdin=self.stream)

    def test_yaml(self):
        self.assertRaises(
            SystemExit, main, argv=["-f", "yaml"], stdin=self.stream)

    def test_dot(self):
        self.assertRaises(
            SystemExit, main, argv=["-f", "dot"], stdin=self.stream)

    def test_dot_with_phase(self):
        self.assertRaises(SystemExit, main, argv=[
                          "-f", "dot", "-p", "normalized"], stdin=self.stream)


class TestTransformResolveErrors(TestCase):

    def setUp(self):
        self.stream = io.StringIO("""
            hello: {{ 5 / 0 }}
            """)

    def test_py(self):
        self.assertRaises(
            SystemExit, main, argv=["-f", "py"], stdin=self.stream)

    def test_yaml(self):
        self.assertRaises(
            SystemExit, main, argv=["-f", "yaml"], stdin=self.stream)
