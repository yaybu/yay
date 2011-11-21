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

from yay.nodes import Node, BoxingFactory, Sequence, Context
from yay.nodes.flatten import flatten


class ForEach(Node):

    """
    Represents an iteration over a sequence or other iterable node.

    This will be added to the graph when the parser encounters the ``.foreach`` function::

        example.foreach fruit in basket if fruit.price = 5: ${fruit.name}
    """

    def __init__(self, root, value, args):
        self.root = root
        self.value = value
        value.set_parent(self)

        self.alias = args.pop(0).strip()

        self.lookup = args.pop(0)
        self.lookup.set_parent(self)

        if len(args) and args[0] in ("chain", "nochain", "flatten"):
            self.mode = args.pop(0)
        else:
            self.mode = "flatten"

        if len(args):
            if args[0] != "if":
                self.error("Expected 'if', got '%s'" % args[0])
            args.pop(0)
            self.filter = args.pop(0)
            self.filter.set_parent(self)
        else:
            self.filter = None

    def expand(self):
        lst = []

        for item in self.lookup.expand():
            c = Context(self.value.clone(), {self.alias: item})
            c.set_parent(self)

            if self.filter:
                f = self.filter.clone()
                f.set_parent(c)
                if not f.resolve():
                    continue

            item.set_parent(c)

            if self.mode == "nochain":
                lst.append(c)
            else:
                c.set_parent(self)
                val = c.resolve()
                if isinstance(val, list):
                    if self.mode == "flatten":
                        lst.extend(BoxingFactory.box(v) for v in flatten(val))
                    else:
                        lst.extend(BoxingFactory.box(v) for v in val)
                else:
                    lst.append(BoxingFactory.box(val))

        sq = Sequence(lst)
        sq.set_parent(self.parent)
        return sq

    def resolve(self):
        return self.expand().resolve()

    def walk(self):
        yield self.lookup
        #yield self.value

    def clone(self):
        fe = ForEach(self.root, self.value.clone(), [self.alias, self.lookup.clone(), self.mode])
        if self.filter:
            fe.filter = self.filter.clone()
            fe.filter.set_parent(fe)
        return fe

