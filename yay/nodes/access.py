# Copyright 2010-2012 Isotoma Limited
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


class Access(Node):

    """
    A future lookup on another part of the graph.

    This node is created when the parser encounters any source of lookup.
    For example::

        foo: ${bar.baz.qux}

    This will create 3 Access nodes. The first will look up ``bar`` using
    :py:meth:`.get_context`. The 2nd will lookup ``baz`` on the object returned
    by the ``bar`` lookup. And so on.

    The lookup won't actually happen until :py:meth:`.resolve` is called. This means
    the graph can still continue to change as more data is loaded.
    """

    def __init__(self, container, access):
        self.container = container
        if container:
            container.set_parent(self)
        self.access = access
        self.access.set_parent(self)

    def get(self, idx):
        sr = self.expand()
        return sr.get(idx)

    def expand(self):
        __context__ = self.context("Resolving key to use as index lookup")

        key = self.access.resolve()

        if self.container:
            __context__ = self.context("Performing lookup of %s", key)

            unresolved = self.container.get(key)
            if unresolved is None:
                self.error("Container does not have field '%s'" % key)
        else:
            __context__ = self.context("Performing lookup of %s on document root", key)

            unresolved = self.get_context(key)
            if unresolved is None:
                self.error("Context does not have field '%s'" % key)

        if hasattr(unresolved, "expand"):
            return unresolved.expand()

        return unresolved

    def resolve(self):
        sr = self.expand()
        return sr.resolve()

    def walk(self):
        yield self.expand()

    def __repr__(self):
        return "Access(%s, %s)" % (self.container, self.access)

    def clone(self):
        c = None
        if self.container:
            c = self.container.clone()
        a = Access(c, self.access.clone())

        a.file = self.name 
        a.line = self.line
        a.column = self.column
        a.snippet = self.snippet

        return a

