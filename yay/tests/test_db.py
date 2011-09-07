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

dbyay = """
metadata.database:
    connection: |
        sqlite:///:memory:
    tables:
      - name: user
        fields:
          - name: id
            type: integer
            pk: True
          - name: username
          - name: password

      - name: host
        fields:
          - name: id
            type: integer
            pk: True
          - name: name
          - name: services

      - name: service
        fields:
          - name: id
            type: integer
            pk: True
          - name: name
            name: branch
"""


class TestDb(unittest.TestCase):

    def setUp(self):
        self.config = Config()
        self.config.load(dbyay)

        #t = Database(c['database'])

        #t.engine = create_engine('sqlite:///:memory:', echo=True)
        #Session = sessionmaker(bind=t.engine)
        #session = Session()

        #T = t.build_table(t.config)

        #Base.metadata.create_all(t.engine)

        #session.add(T(username='john', password='password'))
        #session.add(T(username='john', password='password'))
        #session.add(T(username='john', password='password'))
        #session.add(T(username='john', password='password'))
        #session.add(T(username='john', password='password'))

        #session.commit()

        #print t.resolve()

    def test_list_all(self):
        self.config.get()

