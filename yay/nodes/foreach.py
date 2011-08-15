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

from yay.nodes import Node, Boxed, Sequence, Context

class ForEach(Node):

    def __init__(self, root, value, args):
        self.root = root
        self.value = value
        value.set_parent(self)

        self.lookup = args[1]
        self.lookup.set_parent(self)
        self.alias = args[0].strip()

        print "ForEach", self.value, self.lookup, self.alias

    def semi_resolve(self, context):
        lst = []

        for item in self.lookup.semi_resolve(context):
            c = Context(self.value.clone(), {self.alias: item})
            item.set_parent(c)
            lst.append(c)

        sq = Sequence(lst)
        sq.set_parent(self.parent)
        return sq

    def resolve(self, context):
        return self.semi_resolve(context).resolve(context)

    def walk(self, context):
        yield self.lookup
        #yield self.value

    def clone(self):
        return ForEach(self.root, self.value.clone(), [self.alias, self.lookup.clone()])

