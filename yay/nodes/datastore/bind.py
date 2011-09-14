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
from yay.errors import ProgrammingError

class DataStoreType(type):

    stores = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        name = new_attrs.get('__name__', class_name.lower())
        if name in meta.stores:
            raise ProgrammingError("Redefinition of DataStoreType '%s'" % name)
        meta.stores[name] = cls
        return cls


class DataStore(object):
    __metaclass__ = DataStoreType


class Bind(Node):

    def __init__(self, config):
        self.config = config
        self.backend = None

    def get_backend(self):
        if not self.backend:
            backend_type = self.config.get("type").resolve()
            self.backend = DataStoreType.stores[backend_type](self.config)
        return self.backend

    def get(self, key):
        return self.get_backend().get(key)

    def resolve(self):
        return {}


