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

class Boxed(Node):
    """
    A Boxed variable is an unmodified and uninteresting value that
    is wrapped simply so we can put it in our graph
    """

    def resolve_string(self, context, value):
        encountered = set()
        previous = None
        while value != previous:
            if value in encountered:
                raise ValueError("Cycle encountered (%s)" % label)
            encountered.add(value)

            previous = value
            value = value.format(context)

        return value

    def resolve(self, context):
        if isinstance(self.value, basestring):
            return self.resolve_string(context, self.value)
        return self.value

    def get(self, context, key, default=None):
        return Boxed(self.value.get(key, default))

    def __repr__(self):
        return "Boxed(%s)" % self.value

