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
from yay.protectedstring import ProtectedString

class Boxed(Node):
    """
    A Boxed variable is an unmodified and uninteresting value that
    is wrapped simply so we can put it in our graph
    """

    def __init__(self, value):
        self.value = value

    secret = False

    def resolve(self):
        value = self.value

        if not isinstance(value, basestring):
            return value

        if self.secret:
            p = ProtectedString()
            p.add_secret(value)
            return p

        if value.lower() in ("yes", "true", "on"):
            return True
        if value.lower() in ("no", "false", "off"):
            return False

        try:
            return int(value)
        except ValueError:
            pass

        #FIXME: could still be a float or a timestamp

        try:
            return value.encode('ascii')
        except UnicodeEncodeError:
            return value

    def get(self, key, default=None):
        if isinstance(self.value, list):
            return Boxed(self.value[key])

        return Boxed(self.value.get(key, default))

    def __repr__(self):
        return "Boxed(%s)" % self.value

    def clone(self):
        return Boxed(self.value)

