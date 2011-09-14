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

class Context(Node):

    """
    Add context to the graph.

    Any children of this node will get different context to the parents
    of this node as it implements ``get_context``.
    """

    def __init__(self, value, context):
        super(Context, self).__init__(value)
        self.context = context

    def get_context(self, key):
        """
        If ``key`` is provided by this node return it, otherwise fall
        back to default implementation.
        """
        val = self.context.get(key, None)
        if not val:
            val = super(Context, self).get_context(key)
        return val

    def expand(self):
        return self.value.expand()

    def resolve(self):
        return self.value.resolve()

    def __repr__(self):
        return "Context(%s)" % self.value

    def clone(self):
        return Context(self.value.clone(), self.context)

