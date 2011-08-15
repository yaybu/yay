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

class Select(Node):

    def __init__(self, options, key):
        self.options = options
        options.set_parent(self)
        self.key = key
        key.set_parent(self)

    def expand(self):
        key = self.key.resolve()
        return self.options.get(key)

    def resolve(self):
        return self.expand().resolve()

    def walk(self):
        yield self.key
        yield self.expand()

    def clone(self):
        return Select(self.options.clone(), self.key.clone())

