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

from yay.nodes import Node

class Comparison(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__, self.left, self.right)

class And(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) and self.right.resolve(context)

class Or(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) or self.right.resolve(context)

class In(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) in self.right.resolve(context)

class Equal(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) == self.right.resolve(context)

class NotEqual(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) != self.right.resolve(context)

class LessThan(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) < self.right.resolve(context)

class LessThanEqual(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) <= self.right.resolve(context)

class GreaterThan(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) > self.right.resolve(context)

class GreaterThanEqual(Comparison):
    def resolve(self, context):
        return self.left.resolve(context) >= self.right.resolve(context)


class Access(Node):
    def __init__(self, container, access):
        self.container = container
        self.access = access

    def get(self, context, idx, default=None):
        sr = self.semi_resolve(context)
        return sr.get(context, idx, default)

    def semi_resolve(self, context):
        if self.container:
            return self.container.get(context, self.access)
        return context.get(self.access)

    def resolve(self, context):
        return self.semi_resolve(context).resolve(context)

    #def get(self, context, key, default=None):
    #    self.resolve(context).get(context, key, default)

    def __repr__(self):
        return "Access(%s, %s)" % (self.container, self.access)


class Concatenation(Node):
    def __init__(self, *args):
        self.args = args

    def resolve(self, context):
        return "".join(arg.resolve(context) for arg in self.args)

    def __repr__(self):
        return "Concat(%s)" % ", ".join(str(arg) for arg in self.args)

