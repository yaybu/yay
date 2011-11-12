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
from yay import String


class Secret(Node):

    def __init__(self, value):
        self.value = value
        self.value.set_parent(self)

    def resolve(self):
        r = self.value.resolve()

        if not isinstance(r, basestring):
           self.error("Only simple strings can be marked with .secret at this time. Perhaps you want to look in to .yay.gpg files?")

        p = String()
        p.add_secret(r)
        return p

    def get(self, key):
        return self.value.get(key)

    def __repr__(self):
        return "Secret(%s)" % self.value

    def clone(self):
        return Secret(self.value)

