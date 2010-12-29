import types
import copy

import yaml

from yay.loader import Loader
from yay.ordereddict import OrderedDict
from yay.openers import Openers
from yay.resolver import Resolvable

class Node(object):
    __slots__ = ("chain", "value")
    chain = None

    def __init__(self, value=None):
        # Premature typing optimisation
        self.value = value

    def apply(self, data):
        pass

    def resolve_child(self, child):
        r = child
        while isinstance(r, Node):
            r = r.resolve()
        return r

    def resolve(self):
        data = None
        if self.chain:
            data = self.resolve_child(self.chain)
        return self.apply(data)


class Boxed(Node):
    """
    A Boxed variable is an unmodified and uninteresting value that
    is wrapped simply so we can put it in our graph
    """
    def resolve(self):
        return self.value


class Dictionary(Node):
    """
    I represent a dictionary that will be manufactured out of multiple components
    at resolve time

    We absolutely cannot have 2 Dictionary nodes for the same path, if we would one
    would replace another. That is why we override resolve(), not apply(), and ignore
    previous data
    """
    def __init__(self):
        self.value = {}

    def set(self, key, val):
        val.chain = self.value.get("key", None)
        self.value[key] = val

    def get(self, key, default=None):
        return self.value.get(key, default)

    def resolve(self):
        data = {}
        for key, val in self.value.iteritems():
            data[key] = self.resolve_child(val)
        return data


class List(Node):
    """ 
    I am a list that hasnt been created yet
    """
    def get(self, idx):
        return None

    def resolve(self):
        data = []
        for val in self.value:
            data.append(val.resolve())
        return data


class Lookup(Node):
    """
    I delay a lookup until resolve time
    """
    def __init__(self, value, xformer):
        super(Lookup, self).__init__(value)
        self.xformer = xformer

    def resolve(self):
        # This is derived from string.py Formatter so lookup language
        # is consistent
        # field name parser is written in C and available as
        #   str._formatter_field_name_split()
        first, rest = self.value.resolve()._formatter_field_name_split()
        obj = self.xformer.root.get(first, None)
        for is_attr, i in rest:
            obj = obj.get(i)
        return obj

class Copy(Node):
    """
    I resolve a node and deepcopy the outcome

    I am a replacing node and do not care about data i am overlaying
    """
    def resolve(self):
        return copy.deepcopy(self.value)        
        

class Append(Node):

    def apply(self, existing):
        return existing + self.value

class Remove(Node):

    def apply(self, existing):
        return [x for x in existing if x not in self.value]


class TreeTransformer(object):
    """
    I turn the 'parse trees' (repr'd as ordered dictionarys and other
    primitives) into a compile tree
    """

    def __init__(self):
        self.action_map = {
            "copy": lambda value: Copy(Lookup(value, self)),
            "assign": lambda value: Boxed(value),
            "append": lambda value: Append(value),
            "remove": lambda value: Remove(value),
            }

    def visit(self, container, value):
        assert not isinstance(value, Node)
        if isinstance(value, (dict, OrderedDict)):
            return self.visit_dict(container, value)
        if isinstance(value, list):
            return self.visit_list(value, container)
        return Boxed(value)

    def visit_list(self, value, container):
        data = []
        for v in value:
            data.append(self.visit(container, v))
        return List(data)
 
    def visit_dict(self, container=None, value=None):
        # This feels wrong. I think the approach is fine but the ownership and control flow is a bit of a soggy biscuit
        # Revisit when less ill.

        if not container:
            container = Dictionary()

        if not isinstance(container, Dictionary):
            # FIXME: Think about when better. container used to be something else but isnt now??
            container = Dictionary()

        for key, value in value.iteritems():
            action = "assign"
            if "." in key:
                key, action = key.split(".")

            existing = container.get(key, None)

            # Put the value in a simple box so it can be stored in our tree
            boxed = self.visit(existing, value)

            # Further box the value based on the kind of action it is
            boxed = self.action_map[action](boxed)

            # And add it to the dictionary (which will automatically chain nodes)
            container.set(key, boxed)

        return container

    def transform(self, config):
        self.root = Dictionary()
        for c in config.loaded:
            self.visit_dict(self.root, c)
        return self.root.resolve()

class Config(object):

    def __init__(self, special_term='yay'):
        self.special_term = special_term
        self.openers = Openers()
        self.loaded = []

    def load_uri(self, uri):
        self.load(self.openers.open(uri))

    def load(self, stream):
        data = yaml.load(stream, Loader=Loader)

        special = data.get(self.special_term, None)
        if special:
            for uri in special.get('extends', []):
                self.load_uri(uri)

        self.update(data)

    def update(self, config):
        """
        Recursively update config with a dict
        """
        self.loaded.append(config)

    def clear(self):
        self.loaded = []

    def get(self):
        return TreeTransformer().transform(self)


def load_uri(uri, special_term='yay'):
    c = Config(special_term)
    c.load_uri(uri)
    return c.get()

def load(stream, special_term='yay'):
    c = Config(special_term)
    c.load(stream)
    return c.get()

