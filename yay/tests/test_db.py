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
from yay.nodes import Database

from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


dbyay = """
metadata.database:
    connection: sqlite://
    tables:
      - name: user
        fields:
          - name: id
            type: integer
            pk: True
          - name: username
          - name: password

      - name: service
        fields:
          - name: id
            type: integer
            pk: True
          - name: name
          - name: branch
          - name: host_id
            type: integer
            foreign_key: host.id

      - name: host
        fields:
          - name: id
            type: integer
            pk: True
          - name: name
          - name: services
            relationship: service
"""

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

        t.engine = engine
        t.base.metadata.create_all(engine)

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
        self.t.base.metadata.drop_all(self.t.engine)

    def test_foreach_host(self):
        self.config.load("""
            test.foreach h in metadata.host: ${h.name}
            """)

        self.failUnlessEqual(self.config.get()["test"], ["wonderflonium"])

    def test_list_all(self):
        self.config.get()

