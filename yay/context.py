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

from yay.nodes import Node

class RootContext(object):

    def __init__(self, root):
        self.root = root
        self.functions = {}

        self.functions['range'] = range

    def get(self, key, default=None):
        return self.root.get(self, key, default)

    def call(self, func, args):
        return self.functions[func](*args)

class Context(object):

    def __init__(self, parent, variables):
        self.parent = parent
        self.variables = variables if variables else {}

    def get(self, key, default=None):
        if key in self.variables:
            return self.variables[key]

        if self.parent:
            return self.parent.get(key, default)

        return default

    def call(self, func, args):
        return self.parent.call(func, args)
