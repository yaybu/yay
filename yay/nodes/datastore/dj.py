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

try:
    from django.db import models
    from django.conf import settings
    has_django_db = True
except ImportError:
    has_django_db = False

import inspect

import yay
from yay.nodes import Node, Boxed, Sequence
from yay.nodes.datastore.bind import DataStore


class InstanceList(Node):

    """
    I am a list of Instance nodes - i.e. a one-to-many relationship
    """

    def __init__(self, value):
        self.value = value

    def get(self, idx):
        v = self.value.all()[idx]

        if isinstance(v, models.Model):
            return Instance(v)

        return Boxed(self.values[idx])

    def resolve(self):
        return list(self.__iter__())

    def __iter__(self):
        for i in range(len(self.values)):
            yield self.get(i)


class Instance(Node):

    def __init__(self, value):
        self.value = value

        self.related = [x.get_accessor_name() for x in self.value._meta.get_all_related_objects()]
        self.many_to_many = [x.get_accessor_name() for x in self.value._meta.get_all_related_many_to_manyobjects()]

    def get(self, key):
        v = getattr(self.value, key)

        if isinstance(v, models.Model):
            return Instance(v)

        if key in self.related or key in self.many_to_many:
            return InstanceList(v)

        return Boxed(getattr(self.value, key))

    def resolve(self):
        return dict((k,getattr(self.value,k)) for k in self.value.__table__.columns.keys())


class Table(Node):

    def __init__(self, value):
        self.value = value

    def expand(self):
        seq = []

        for instance in self.value.objects.all():
             seq.append(Instance(instance))

        return Sequence(seq)

    def resolve(self):
        return self.expand().resolve()


class DjangoStore(DataStore):

    def __init__(self, config):
        self.config = config
        self.tables = {}

    def get_model(self, key):
        model = self.config.get("model").resolve()
        __import__(model)
        m = sys.modules[model]

        if not key in dir(m):
            self.error("Model '%s' not defined in '%s'" % (key, model))

        v = getattr(m, k)

        if not inspect.isclass(thing) or not issubclass(thing, models.Model):
            self.error("'%s' is defined in '%s', but it isn't a Django model" % (key, model))

        return Table(self, v)

    def get(self, key):
        if key in self.tables:
            return self.tables[key]

        if self.config.get("model"):
            tbl = self.tables[key] = self.get_model(key)
            return tbl

        self.error("'model' not specified")

