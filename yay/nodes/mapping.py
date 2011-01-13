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

class Mapping(Node):
    """
    I represent a dictionary that will be manufactured out of multiple components
    at resolve time
    """
    def __init__(self, predecessor):
        self.predecessor = predecessor
        self.value = {}

    def set(self, key, val):
        #val.chain = self.value.get("key", None)
        self.value[key] = val

    def get(self, context, key, default=None):
        if key in self.value:
            return self.value[key]
        if self.predecessor:
            return self.predecessor.get(context, key, default)
        return default

    def keys(self):
        keys = set(self.value.keys())
        if self.predecessor:
            keys.update(self.predecessor.keys())
        return list(keys)

    def resolve(self, context):
        data = {}
        for key in self.keys():
            data[key] = self.get(context, key, None).resolve(context)
        return data

