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

from yay.nodes import Node, BoxingFactory
from yay.errors import NoMatching

class Mapping(Node):

    """
    An unordered collection of key/value pairs
    """

    def __init__(self, predecessor):
        self.predecessor = predecessor
        if predecessor:
            predecessor.set_parent(self)
        self.value = {}

    def set(self, key, val):
        #val.chain = self.value.get("key", None)
        self.value[key] = val
        val.set_parent(self)

    def get(self, key):
        if key in self.value:
            return self.value[key]
        if self.predecessor:
            return self.predecessor.get(key)
        self.error(NoMatching("Not found: '%s'" % key))

    def keys(self):
        keys = set(self.value.keys())
        if self.predecessor:
            keys.update(self.predecessor.expand().keys())
        return list(keys)

    def resolve(self):
        data = {}
        for key in self.keys():
            try:
                key = key.encode('ascii')
            except UnicodeEncodeError:
                pass

            data[key] = self.get(key).resolve()
        return data

    def walk(self):
        for itm in self.value.items():
            yield itm
        yield self.predecessor

    def clone(self):
        p = None
        if self.predecessor:
            p = self.predecessor.clone()

        m = Mapping(p)
        for k, v in self.value.items():
            m.set(k, v.clone())
        return m

    def __iter__(self):
        return iter(BoxingFactory.box(v) for v in sorted(self.keys()))


def box_dict(val):
    m = Mapping(None)
    for k, v in val.items():
        m.set(k, BoxingFactory.box(v))
    return m
BoxingFactory.register(lambda x: isinstance(x, dict), box_dict)

