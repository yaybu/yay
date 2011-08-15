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
    __slots__ = ("chain", "value")
    chain = None
    parent = None
    locked = False

    name = "<Unknown>"
    line = 0
    column = 0
    snippet = None

    def __init__(self, value=None):
        # Premature typing optimisation
        self.value = value
        value.set_parent(self)

    def set_parent(self, parent):
        self.parent = parent

    def resolve(self):
        raise NotImplementedError(self.resolve)

    def expand(self):
        return self

    def walk(self):
        return iter([])

    def lock(self):
        self.locked = True
        for child in self.walk():
            child.lock()

    def get_context(self, key):
        if self.parent:
            return self.parent.get_context(key)
        else:
            return self.expand().get(key)

    def get_root(self):
        if self.parent:
            return self.parent.get_root()
        else:
            return self

    def error(self, message):
        raise EvaluationError(
            message,
            self.name,          # File
            self.line,          # Line
            self.column,        # Column
            self.snippet)       # Snippet

    def clone(self):
        raise NotImplementedError(self.clone)

    def __str__(self):
        return repr(self)

