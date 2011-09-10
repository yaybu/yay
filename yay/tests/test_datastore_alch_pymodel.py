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


import unittest
import yay
from yay.config import Config

from sqlalchemy import Column, ForeignKey, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

dbyay = """
metadata.bind:
    type: sqlalchemy
    connection: sqlite://
    model: yay.tests.test_datastore_alch_pymodel
"""

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)

class Service(Base):
    __tablename__ = "service"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    branch = Column(String)
    host_id = Column(Integer, ForeignKey('host.id'))

class Host(Base):
    __tablename__ = "host"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    services = relationship('Service')


engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)
session = Session()


class TestDb(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.load(dbyay)

        self.t = t = self.config.mapping.get('metadata')

        User = t.get("user").value
        Service = t.get("service").value
        Host = t.get("host").value

        t.backend.engine = engine
        Base.metadata.create_all(engine)

        session.add(User(username='john', password='password'))
        session.add(User(username='john', password='password'))
        session.add(User(username='john', password='password'))
        session.add(User(username='john', password='password'))
        session.add(User(username='john', password='password'))

        h = Host(name="wonderflonium")
        session.add(h)

        s = Service(name="www.foo.com", branch="/trunk")
        h.services.append(s)
        session.add(s)

        session.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.t.backend.engine)

    def test_foreach_host(self):
        self.config.load("""
            test.foreach h in metadata.host: ${h.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ["wonderflonium"])

    def test_foreach_host_service(self):
        self.config.load("""
            test.foreach h in metadata.host:
              .foreach s in h.services: ${s.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ["www.foo.com"])

    def test_foreach_host_service_if(self):
        self.config.load("""
            branch: /trunk
            test.foreach h in metadata.host:
              .foreach s in h.services if s.branch=branch: ${s.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ["www.foo.com"])

    def test_foreach_host_service_if_failing(self):
        self.config.load("""
            branch: /trun
            test.foreach h in metadata.host:
              .foreach s in h.services if s.branch=branch: ${s.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], [])

