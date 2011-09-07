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

from StringIO import StringIO

try:
    from sqlalchemy import Column, String, Integer, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    has_sqlalchemy = True
except ImportError:
    has_sqlalchemy = False

import yay
from yay.nodes import Node, Boxed, Sequence

class Instance(Node):

    def __init__(self, value):
        self.value = value

    def get(self, key):
        return Boxed(getattr(self.value, key))

    def resolve(self):
        return dict((k,getattr(self.value,k)) for k in self.value.__table__.columns.keys())


class Database(Node):

    engine = None
    base = declarative_base()

    def __init__(self, config):
        self.config = config

    def build_column(self, columnspec):
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

        column = Column(T(), primary_key=primary_key)
        return column

    def build_table(self, config):
        if not "name" in config:
            self.error("Table name is not given")

        if not "fields" in config:
            self.error("Field list is missing from definition")

        if not isinstance(config["fields"], list):
            self.error("Fiel list should be a list of column definitions")

        attrs = {}
        attrs['__tablename__'] = config['name']
        attrs['__table_args__'] = dict(
            useexisting = True,
            )

        for c in config["fields"]:
            attrs[c["name"]] = self.build_column(c)

        table = type(config["name"], (self.base,), attrs)
        return table

    def expand(self):
        if not has_sqlalchemy:
            self.error("You are attempting to use a database from Yay, but SQLAlchemy is not installed")

        tbl = self.build_table(self.config.get("tables").resolve()[0])

        if not self.engine:
            self.engine = create_engine(self.config.get("connection").resolve(), echo=True)
        Session = sessionmaker(bind=self.engine)
        session = Session()

        seq = []

        for instance in session.query(tbl).all():
             seq.append(Instance(instance))

        return Sequence(seq)

    def resolve(self):
        return self.expand().resolve()


