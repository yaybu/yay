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

from yay.nodes import Node, BoxingFactory

def sum(*args):
    return reduce(lambda x, y: x+y, args)


class Function(Node):

    """
    Created when the parser encounters something that looks like a function call::

        example.foreach i in range(5): ${i}
    """

    functions = {
        "range": range,
        "sum": sum,
        }

    def __init__(self, function, args):
        self.function = function
        self.args = args
        [x.set_parent(self) for x in args]

    def resolve(self):
        args = [arg.resolve() for arg in self.args]
        return self.functions[self.function](*args)

    def expand(self):
        return [BoxingFactory.box(x) for x in self.resolve()]

    def __repr__(self):
        return "Function(%s)" % ", ".join([self.function] + [str(a) for a in self.args])

    def walk(self):
        for arg in self.args:
            yield arg

    def clone(self):
        return Function(self.function, [x.clone() for x in self.args])

