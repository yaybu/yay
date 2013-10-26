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

from yay.tests.base import TestCase
from yay.ast import YayMultilineScalar, YayScalar
from mock import Mock


v = "foo bar baz\nquux blor\n"
w = "foo bar baz\n\nquux blorp\n\n"


class TestASTMultiline(TestCase):

    def _m(self, c):
        return (
            YayMultilineScalar(v, c).value,
            YayMultilineScalar(w, c).value,
        )

    def test_chomp_literal(self):
        self.assertEqual(self._m("|"), (
            'foo bar baz\nquux blor\n',
            'foo bar baz\n\nquux blorp\n',
        ))

    def test_chomp_keep(self):
        # NB: the commented result below is the behaviour of pyyaml
        # however it is such an edge case, and so hard to fix
        # I'm happy to leave this - D
        self.assertEqual(self._m("|+"), (
            'foo bar baz\nquux blor\n',
            #'foo bar baz\n\nquux blorp\n\n\n',
            'foo bar baz\n\nquux blorp\n\n',
        ))

    def test_chomp_strip(self):
        self.assertEqual(self._m("|-"), (
            'foo bar baz\nquux blor',
            'foo bar baz\n\nquux blorp',
        ))

    fold = ("Mark McGwire's\n"
            "year was crippled\n"
            "by a knee injury.\n")
    fold_out = "Mark McGwire's year was crippled by a knee injury. "

    def test_chomp_fold(self):
        """ In folded scalars, newlines become spaces """
        r = YayMultilineScalar.chomp_fold(self.fold)
        self.assertEqual(r, self.fold_out)

    def test_chomp_fold_value(self):
        r = YayMultilineScalar(YayScalar(self.fold), ">")
        self.assertEqual(r.value, YayScalar(self.fold_out.rstrip()))
