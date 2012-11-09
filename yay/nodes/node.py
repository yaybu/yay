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

from yay.errors import EvaluationError


class Node(object):

    """
    The base class for all things that can be inserted into the graph.
    """

    __slots__ = ("value", "parent", "predecessor")

    name = "<Unknown>"
    line = 0
    column = 0
    snippet = None

    def __init__(self):
        self.parent = None
        self.predecessor = None

    def set_parent(self, parent):
        self.parent = parent

    def set_predecessor(self, predecessor):
        self.predecessor = predecessor

    def resolve(self):
        """
        Resolve an object into a simple type, like a string or a dictionary.

        Node does not provide an implementation of this, all subclasses should
        implemented it.
        """
        raise NotImplementedError(self.resolve)

    def expand(self):
        """
        Generate a simplification of this object that can replace it in the graph
        """
        return self

    def get_context(self, key):
        """
        Look up value of ``key`` and return it.

        This doesn't do any resolving, the return value will be a subclass of Node.
        """
        if self.parent:
            return self.parent.get_context(key)
        else:
            return self.expand().get(key)

    def get_root(self):
        """
        Find and return the root of this document.
        """
        if self.parent:
            return self.parent.get_root()
        else:
            return self

    def error(self, exc):
        """
        Raise an error message annotated with the line and column of the text that was
        parsed to create this node
        """
        if isinstance(exc, basestring):
            exc = EvaluationError(exc)

        exc.file = self.name            # File
        exc.line = self.line            # Line
        exc.column = self.column        # Column
        exc.snippet = self.snippet      # Snippet

        raise exc

    def context(self, msg, *args):
        """
        Attack debug context to the stack

        """
        msg = msg % args
        return "%s (file: %s, line: %s, column: %s)" % (msg, self.name, self.line, self.column)

    def __str__(self):
        return repr(self)

