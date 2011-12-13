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
from yay.errors import NoMatching


class Call(Node):

    def __init__(self, composer, value, params=None):
        self.composer = composer
        self.value = value
        self.params = params
        if params:
            params.set_parent(self)

    def get_context(self, label):
        if self.params:
            try:
                return self.params.expand().get(label)
            except NoMatching:
                pass
        return super(Call, self).get_context(label)

    def get(self, idx):
        return self.expand().get(idx)

    def expand(self):
        try:
            block = self.composer.parent.definitions[self.value]
        except KeyError:
            self.error("'%s' was not defined" % self.value)

        clone = block.clone()
        clone.set_parent(self)

        return clone.expand()

    def resolve(self):
        return self.expand().resolve()

    def walk(self):
        yield self.value

    def clone(self):
        return Call(self.composer, self.value, self.params.clone() if self.params else None)

