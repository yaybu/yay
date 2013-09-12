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

from .base import TestCase, parse, resolve
from yay import errors


class TestResolveCycles(TestCase):

    def test_self_recursion(self):
        res = parse("""
            foo: {{ foo }}
            """)
        self.assertRaises(errors.CycleError, str, res.foo)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_templated_self_recursion(self):
        res = parse("""
            foo: hello {{ foo }}
            """)
        self.assertRaises(errors.CycleError, str, res.foo)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_addition_self_recursion(self):
        res = parse("""
            foo: {{ 1 + foo }}
            """)
        self.assertRaises(errors.CycleError, int, res.foo)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_flip_flop(self):
        res = parse("""
            flip: {{ flop }}
            flop: {{ flip }}
            """)
        self.assertRaises(errors.CycleError, int, res.flip)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_flip_flop_with_nesting(self):
        res = parse("""
            flip:
                inside: {{ flop.inside }}
            flop:
                inside: {{ flip.inside }}
            """)
        self.assertRaises(errors.CycleError, int, res.flip.inside)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_flip_flop_flap(self):
        res = parse("""
            flip: {{ flap }}
            flop: {{ flip }}
            flap: {{ flop }}
            """)
        self.assertRaises(errors.CycleError, int, res.flap)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_flip_flop_flap_with_nesting(self):
        res = parse("""
            flip:
                inside: {{ flap.inside }}
            flop:
                inside: {{ flip.inside }}
            flap:
                inside: {{ flop.inside }}
            """)
        self.assertRaises(errors.CycleError, int, res.flap.inside)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_iterable_cycle(self):
        res = parse("""
            foo:
              - foo
              - {{ foo[1] }}
            """)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_iterable_cycle_with_indirection(self):
        res = parse("""
            bar: {{ foo }}
            foo:
              - foo
              - {{ bar[1] }}
            """)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_oh_dear_well_it_isnt_a_cycle_exactly(self):
        res = parse("""
            foo:
              - foo
              - {{ foo[0] }}
            """)
        self.assertEqual(res.foo.resolve(), ['foo', 'foo'])

    def test_oh_dear_oh_dear(self):
        res = parse("""
            bar: {{ foo }}
            foo:
              - foo
              - {{ bar[0] }}
            """)
        self.assertEqual(res.foo.resolve(), ['foo', 'foo'])

    def test_if(self):
        res = parse("""
            flip: 1
            flop: {{ flip }}
            if flop:
                flip: {{ flop }}
            """)
        self.assertRaises(errors.CycleError, int, res.flip)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_oh_please_make_it_stop(self):
        res = parse("""
            flip: {{ inside.loft }}

            foo: {{ flop }}

            flop:
                - foo
                - {{ flip }}
                - {{ foo[1] }}

            if flop[0]:
                inside:
                    outside: {{ flop[2] }}
                    loft: {{ here.outside }}

            """)
        self.assertRaises(errors.CycleError, str, res.flip)
        self.assertRaises(errors.CycleError, res.resolve)

    def test_set_loop(self):
        res = parse("""
            set a = b
            set b = a

            foo: {{ a }}
            """)
        self.assertRaises(errors.CycleError, str, res.foo)
        self.assertRaises(errors.CycleError, res.resolve)
