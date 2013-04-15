
from functools import partial


class Edge(object):

    def __init__(self, from_, to_, label, reverse_label=None):
        self.from_ = from_
        self.to_ = to_
        self.label = label

        self._aliases = []
        self.connect()

    def add_alias(self, obj, key, val):
        setattr(obj, key, val)
        self._aliases.append((obj, key))

    def connect(self):
        self.from_._outgoing.append(self)
        self.to_._incoming.append(self)

    def disconnect(self):
        self.from_._outgoing.remove(self)
        self.to_._incoming.remove(self)

        for obj, key in self._aliases:
            setattr(obj, key, None)


class EdgeProperty(object):

    def contribute_to_class(self, cls, key):
        self.name = key
        self.attr_name = "_" + self.name
        setattr(cls, self.name, self)
        setattr(cls, self.attr_name, None)


class Incoming(EdgeProperty):

    def __get__(self, instance, instance_type=None):
        if not instance:
            return self
        return getattr(instance, self.attr_name).from_

    def __set__(self, instance, value):
        raise ValueError("This property is read-only, bitches.")


class Outgoing(EdgeProperty):

    def __init__(self, incoming=None):
        self.incoming = incoming

    def __get__(self, instance, instance_type=None):
        if not instance:
            return self
        return getattr(instance, self.attr_name).to_

    def __set__(self, instance, value):
        if not instance:
            raise AttributeError("%s must be accessed via instance" % self.name)
        cur = getattr(instance, self.attr_name, None)
        if cur:
            cur.disconnect()
        e = Edge(instance, value, self.name)
        e.add_alias(e.from_, self.attr_name, e)
        if self.incoming:
            e.add_alias(e.to_, "_"+self.incoming, e)


class Child(Outgoing):

    def __init__(self, incoming="parent"):
        super(Child, self).__init__(incoming)


class NodeType(type):

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, {})
        for k, v in new_attrs.items():
            if hasattr(v, "contribute_to_class"):
                v.contribute_to_class(cls, k)
            else:
                setattr(cls, k, v)
        return cls


class Node(object):
    __metaclass__ = NodeType

    parent = Incoming()
    successor = Incoming()
    predecessor = Outgoing(incoming="successor")

    @property
    def q(self):
        return Start(self)

    def __init__(self, **kwargs):
        self._incoming = []
        self._outgoing = []

        for k in kwargs:
            if isinstance(getattr(self.__class__, k), Outgoing):
                setattr(self, k, kwargs[k])
