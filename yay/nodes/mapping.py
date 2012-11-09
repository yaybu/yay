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

class MappingPromise(Node):

    def __init__(self, mapping, key):
        super(MappingPromise, self).__init__()
        self.mapping = mapping
        self.key = key

    def expand(self):
        self.error(NoMatching("Not found: '%s'" % self.key))


class Mapping(Node):

    """
    An unordered collection of key/value pairs
    """

    def __init__(self):
        super(Mapping, self).__init__()
        self.value = {}

    def set(self, key, val):
        #val.chain = self.value.get("key", None)
        self.value[key] = val
        val.set_parent(self)

    def update(self, d):
        if isinstance(d, Mapping):
            for k in d.keys():
                value = d.get(k)
                if k in self.keys():
                    value.predecessor = self.get(k)
                self.set(k, value)

    def get(self, key):
        if key in self.value:
            return self.value[key]
        if self.predecessor:
            return self.predecessor.expand().get(key)
        return MappingPromise(self, key)

    def keys(self):
        keys = set(self.value.keys())
        if self.predecessor:
            try:
                expanded = self.predecessor.expand()
            except NoMatching:
                # this node doesn't have a predecessor
                pass
            else:
                expanded = self.predecessor.expand()
                if not hasattr(expanded, "keys"):
                    self.error("Mapping cannot mask or replace field with same name and different type")
                keys.update(expanded.keys())
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

    def __iter__(self):
        return iter(BoxingFactory.box(v) for v in sorted(self.keys()))


def box_dict(val, predecessor=None):
    m = Mapping(predecessor)
    for k, v in val.items():
        try:
            p = m.get(k)
        except NoMatching:
            p = None

        m.set(k, BoxingFactory.box(v, p))
    return m
BoxingFactory.register(lambda x: isinstance(x, dict), box_dict)

