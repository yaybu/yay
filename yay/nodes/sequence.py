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

import inspect
from yay.nodes import Node, BoxingFactory

class Sequence(Node):

    """
    An ordered list of unresolved :py:class:`~yay.nodes.Node` objects.
    """

    def __init__(self, value=()):
        super(Sequence, self).__init__()
        self.value = list(value)
        [x.set_parent(self) for x in self.value]

    def extend(self, iterable):
        for row in iterable:
            self.value.append(row)
            row.set_parent(self)

    def get(self, idx):
        try:
            idx = int(idx)
        except ValueError:
            self.error("Expected integer but got '%s'" % idx)

        if idx < 0:
            self.error("Index must be greater than 0")
        elif idx >= len(self.value):
            self.error("Index out of range")

        return self.value[idx]

        #b = BoxingFactory.box(self.resolve()[int(idx)])
        #return b

    def resolve(self):
        data = []
        for val in self.value:
            data.append(val.resolve())
        return data

    def __iter__(self):
        return iter(self.value)


def box_generator(val, predecessor=None):
    return Sequence(list(BoxingFactory.box(itm) for itm in val))
BoxingFactory.register(inspect.isgenerator, box_generator)

BoxingFactory.register(lambda x: isinstance(x, list), box_generator)

