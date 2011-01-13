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

from yay.nodes import Node, Filter

class Lookup(Node):
    """
    I delay a lookup until resolve time
    """
    def __init__(self, root, value):
        super(Lookup, self).__init__(value)
        self.root = root

    def split(self, strng):
        return strng._formatter_field_name_split()

    def join(self, first, rest):
        parts = [first]
        for is_attr, i in rest:
            if is_attr:
                parts.append(".%s" % i)
            else:
                parts.append("[%s]" % i)
        return "".join(parts)

    def semi_resolve(self, context):
        # This is derived from string.py Formatter so lookup language
        # is consistent
        # field name parser is written in C and available as
        #   str._formatter_field_name_split()
        handled = []

        first, rest = self.value.resolve(context)._formatter_field_name_split()
        obj = self.root.get(context, first, None)
        if not obj:
            raise KeyError("Unable to find '%s'" % self.join(first, handled))

        for is_attr, i in rest:
            handled.append((is_attr, i))
            if not is_attr:
                obj = Filter(obj, i).resolve(context)
            else:
                obj = obj.get(context, i)
            if not obj:
                raise KeyError("Unable to find '%s'" % self.join(first, handled))

        return obj

    def get(self, context, idx, default):
        return self.semi_resolve(context).get(context, idx, default)

    def resolve(self, context):
        return self.semi_resolve(context).resolve(context)

