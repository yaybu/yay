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

from yay.nodes import Node, BoxingFactory, Sequence

class Append(Node):

    """
    Appends an iterable to a sequence

    This gets added to the graph when the parser encounters an ``append`` function::

        example.append:
          - foo
          - bar

    If ``example`` hasn't been previously defined it behaves as if it is append
    to an empty sequence.
    """

    def get(self, idx, default=None):
        return BoxingFactory.box(self.resolve()[int(idx)])

    def expand(self):
        if not self.chain:
            return self.value.expand()
        # we initialize this sequence weirdly as we dont want to reparent the nodes we are appending
        s = Sequence([])
        s.value = list(iter(self.chain.expand())) + list(iter(self.value.expand()))
        s.set_parent(self.parent)
        return s

    def resolve(self):
        return self.expand().resolve()

    def walk(self):
        yield self.chain
        yield self.value

    def clone(self):
        a = Append(self.value.clone())
        a.chain = self.chain.clone() if self.chain else None
        return a

