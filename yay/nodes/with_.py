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

class With(Node):

    def __init__(self, value, expression, label):
        super(With, self).__init__(value)
        self.expression = expression
        expression.set_parent(self)
        self.label = label

    def get_context(self, key):
        if key == self.label:
            return self.expression
        return super(With, self).get_context(key)

    def expand(self):
        return self.value.expand()

    def resolve(self):
        return self.value.resolve()

    def __repr__(self):
        return "With(%s)" % self.value

    def clone(self):
        return With(self.value.clone(), self.label_)

