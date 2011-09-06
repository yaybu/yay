from StringIO import StringIO
import yay

from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from yay.nodes import Node, Boxed, Sequence

c = yay.load(StringIO("""
database:
    name: user
    schema:
      - name: id
        type: integer
        pk: True
      - name: username
        type: string
      - name: password
        type: string
"""))



Base = declarative_base()

class Instance(Node):

    def __init__(self, value):
        self.value = value

    def get(self, key):
        return Boxed(getattr(self.value, key))

    def resolve(self):
        return dict((k,getattr(self.value,k)) for k in self.value.__table__.columns.keys())


class Database(Node):

    engine = None

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

        if not "schema" in config:
            self.error("Schema is missing from definition")

        if not isinstance(config["schema"], list):
            self.error("Schema should be a list of column definitions")

        attrs = {}
        attrs['__tablename__'] = config['name']
        attrs['__table_args__'] = dict(
            useexisting = True,
            )

        for c in config["schema"]:
            attrs[c["name"]] = self.build_column(c)

        table = type(config["name"], (Base,), attrs)
        return table

    def expand(self):
        tbl = self.build_table(self.config)

        #if not self.engine:
        #    self.engine = create_engine('sqlite:///:memory:', echo=True)
        Session = sessionmaker(bind=self.engine)
        session = Session()

        seq = []

        for instance in session.query(tbl).all():
             seq.append(Instance(instance))

        return Sequence(seq)

    def resolve(self):
        return self.expand().resolve()

t = Database(c['database'])

t.engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=t.engine)
session = Session()


T = t.build_table(t.config)

Base.metadata.create_all(t.engine)

session.add(T(username='john', password='password'))
session.add(T(username='john', password='password'))
session.add(T(username='john', password='password'))
session.add(T(username='john', password='password'))
session.add(T(username='john', password='password'))

session.commit()

print t.resolve()

