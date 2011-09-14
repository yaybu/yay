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

    """
    Configure access to an external data store such as a database for
    access by Yay.

    This node is added to the graph when the parser encounters a ``bind`` function::

        mydb.bind:
            type: somebackend
            arg1: foo
            arg2: bar

    Bind finds an implementation of :py:class:`~yay.nodes.datastore.bind.DataStoreType`
    that has a name of ``somebackend`` and passes all other configuration to it.
    """

    def __init__(self, config):
        self.config = config
        self.backend = None

    def get_backend(self):
        if not self.backend:
            backend_type = self.config.get("type").resolve()
            self.backend = DataStoreType.stores[backend_type](self.config)
        return self.backend

    def get(self, key):
        """
        If a node tries to traverse inside this node we ask the backend for that key
        """
        return self.get_backend().get(key)

    def resolve(self):
        """
        If you try to resolve this node you get an empty mapping. Ideally you would
        get your expanded DataStore, but it could be a massive database so we decided
        not to bother.
        """
        return {}


