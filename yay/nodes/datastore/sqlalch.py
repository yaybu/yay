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

import sys
from StringIO import StringIO

try:
    from sqlalchemy import Column, ForeignKey, String, Integer, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.orm.collections import InstrumentedList
    has_sqlalchemy = True
except ImportError:
    has_sqlalchemy = False

import yay
from yay.nodes import Node, Boxed, Sequence
from yay.nodes.datastore.bind import DataStore

class InstanceList(Node):

    """
    I am a list of Instance nodes - i.e. a one-to-many relationship
    """

    def __init__(self, values):
        self.values = values

    def get(self, idx):
        v = self.values[idx]

        if hasattr(v, "__tablename__"):
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

    def get(self, key):
        v = getattr(self.value, key)

        if hasattr(v, "__tablename__"):
            return Instance(v)

        if isinstance(v, InstrumentedList):
            return InstanceList(v)

        return Boxed(getattr(self.value, key))

    def resolve(self):
        return dict((k,getattr(self.value,k)) for k in self.value.__table__.columns.keys())


class Table(Node):

    def __init__(self, db, value):
        self.db = db
        self.value = value

    def expand(self):
        seq = []

        for instance in self.db.session.query(self.value).all():
             seq.append(Instance(instance))

        return Sequence(seq)

    def resolve(self):
        return self.expand().resolve()


class SQLAlchemy(DataStore):

    def __init__(self, config):
        self.config = config
        self.tables = {}
        self.engine = None
        self._session = None
        self.base = declarative_base()

    def build_column(self, columnspec):
        if "relationship" in columnspec:
            return relationship(columnspec["relationship"])

        types = dict(
            string=String,
            integer=Integer,
            )

        typename = columnspec.get("type", "string")
        try:
            T = types[typename]
        except KeyError:
            self.error("Schema type '%s' is invalid" % typename)

        if "pk" in columnspec and columnspec["pk"]:
            primary_key = True
        else:
            primary_key = False

        args = [T()]

        if "foreign_key" in columnspec:
            args.append(ForeignKey(columnspec['foreign_key']))

        column = Column(*args, primary_key=primary_key)
        return column

    def build_table(self, config):
        if not "name" in config:
            self.error("Table name is not given")

        if not "fields" in config:
            self.error("Field list is missing from definition")

        if not isinstance(config["fields"], list):
            self.error("Field list should be a list of column definitions")

        attrs = {}
        attrs['__tablename__'] = config['name']
        attrs['__table_args__'] = dict(
            useexisting = True,
            )

        for c in config["fields"]:
            attrs[c["name"]] = self.build_column(c)

        table = type(config["name"], (self.base,), attrs)
        return Table(self, table)

    def get_model(self, key):
        model = self.config.get("model").resolve()
        __import__(model)
        m = sys.modules[model]
        for k in dir(m):
            v = getattr(m, k)
            if hasattr(v, "__tablename__") and getattr(v, "__tablename__") == key:
                return Table(self, v)
        #raise NotFound("Table '%s' not defined in '%s'" % (key, model))
        assert False

    def get(self, key):
        if key in self.tables:
            return self.tables[key]

        try:
            if self.config.get("model"):
                tbl = self.tables[key] = self.get_model(key)
                return tbl
        except:
            pass

        for t in self.config.get("tables").resolve():
            if t["name"] == key:
                tbl = self.tables[key] = self.build_table(t)
                return tbl

    @property
    def session(self):
        if self._session:
            return self._session

        if not has_sqlalchemy:
            self.error("You are attempting to use a database from Yay, but SQLAlchemy is not installed")

        if not self.engine:
            self.engine = create_engine(self.config.get("connection").resolve(), echo=True)
        Session = sessionmaker(bind=self.engine)
        self._session = Session()

        return self._session

