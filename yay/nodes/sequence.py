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

    def __init__(self, value):
        self.value = value
        [x.set_parent(self) for x in value]

    def get(self, idx):
        return self.value[int(idx)]
        #b = BoxingFactory.box(self.resolve()[int(idx)])
        #return b

    def resolve(self):
        data = []
        for val in self.value:
            data.append(val.resolve())
        return data

    def __iter__(self):
        return iter(self.value)

    def walk(self):
        for val in self.value:
            yield val

    def clone(self):
        return Sequence([x.clone() for x in self.value])


def box_generator(val):
    return Sequence(list(BoxingFactory.box(itm) for itm in val))
BoxingFactory.register(inspect.isgenerator, box_generator)

BoxingFactory.register(lambda x: isinstance(x, list), box_generator)

