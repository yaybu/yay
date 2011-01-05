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

import types
import copy

import yaml

from yay.loader import Loader
from yay.ordereddict import OrderedDict
from yay.openers import Openers
from yay.resolver import Resolver

class Node(object):
    __slots__ = ("chain", "value")
    chain = None

    def __init__(self, value=None):
        # Premature typing optimisation
        self.value = value

    def apply(self, data):
        pass

    def resolve(self):
        data = None
        if self.chain:
            data = self.chain.resolve()
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
    """
    def __init__(self, predecessor):
        self.predecessor = predecessor
        self.value = {}

    def set(self, key, val):
        #val.chain = self.value.get("key", None)
        self.value[key] = val

    def get(self, key, default=None):
        if key in self.value:
            return self.value.get(key)
        if self.predecessor:
            return self.predecessor.get(key, default)
        return default

    def keys(self):
        keys = set(self.value.keys())
        if self.predecessor:
            keys.update(self.predecessor.keys())
        return list(keys)

    def resolve(self):
        data = {}
        for key in self.keys():
            data[key] = self.get(key).resolve()
        return data


class List(Node):
    """ 
    I am a list that hasnt been created yet
    """
    def get(self, idx, default=None):
        return Boxed(self.resolve()[int(idx)])

    def resolve(self):
        data = []
        for val in self.value:
            data.append(val.resolve())
        return data


class Lookup(Node):
    """
    I delay a lookup until resolve time
    """
    def __init__(self, root, value):
        super(Lookup, self).__init__(value)
        self.root = root

    def split(self, strng):
        return strng._formatter_field_name_split()

    def join(self, first, rest):
        parts = [first]
        for is_attr, i in rest:
            if is_attr:
                parts.append(".%s" % i)
            else:
                parts.append("[%s]" % i)
        return "".join(parts)

    def semi_resolve(self):
        # This is derived from string.py Formatter so lookup language
        # is consistent
        # field name parser is written in C and available as
        #   str._formatter_field_name_split()
        handled = []

        first, rest = self.value.resolve()._formatter_field_name_split()
        obj = self.root.get(first, None)
        if not obj:
            raise KeyError("Unable to find '%s'" % self.join(first, handled))

        for is_attr, i in rest:
            handled.append((is_attr, i))
            obj = obj.get(i)
            if not obj:
                raise KeyError("Unable to find '%s'" % self.join(first, handled))

        return obj

    def get(self, idx, default):
        return self.semi_resolve().get(idx, default)

    def resolve(self):
        return self.semi_resolve().resolve()

class Copy(Node):
    """
    I resolve a node and deepcopy the outcome

    I am a replacing node and do not care about data i am overlaying
    """
    def get(self, idx, default=None):
        return self.value.get(idx, default)

    def resolve(self):
        return copy.deepcopy(self.value.resolve())


class Append(Node):

    def get(self, idx, default=None):
        return Boxed(self.resolve()[int(idx)])

    def apply(self, existing):
        if not existing:
            existing = []
        return existing + self.value.resolve()

class Remove(Node):

    def get(self, idx, default=None):
        return Boxed(self.resolve()[int(idx)])

    def apply(self, existing):
        if not existing:
            return []
        return [x for x in existing if x not in self.value.resolve()]


class TreeTransformer(object):
    """
    I turn the 'parse trees' (repr'd as ordered dictionarys and other
    primitives) into a compile tree
    """

    def __init__(self):
        self.root = None
        self.action_map = {
            "copy": lambda value: Copy(Lookup(self, value)),
            "assign": lambda value: value if isinstance(value, Node) else Boxed(value),
            "append": lambda value: Append(value),
            "remove": lambda value: Remove(value),
            }

    def visit(self, existing_value, new_value):
        assert not isinstance(new_value, Node)

        if isinstance(new_value, (dict, OrderedDict)):
            return self.visit_dict(existing_value, new_value)
        if isinstance(new_value, list):
            return self.visit_list(new_value, existing_value)

        return Boxed(new_value)

    def visit_list(self, new_value, existing_value):
        data = []
        for v in new_value:
            data.append(self.visit(None, v))
        return List(data)

    def visit_dict(self, existing_value, new_value):
        # This feels wrong. I think the approach is fine but the ownership and control flow is a bit of a soggy biscuit
        # Revisit when less ill.

        container = Dictionary(existing_value)

        for key, value in new_value.iteritems():
            action = "assign"
            if "." in key:
                key, action = key.split(".")

            existing = container.get(key, None)

            # Put the value in a simple box so it can be stored in our tree
            boxed = self.visit(existing, value)

            # Further box the value based on the kind of action it is
            boxed = self.action_map[action](boxed)

            # Make sure that Appends are hooked up to correct List
            boxed.chain = existing

            # And add it to the dictionary (which will automatically chain nodes)
            container.set(key, boxed)

        return container

    def update(self, config):
        self.root = self.visit_dict(self.root, config)

    def get(self, key, default=None):
        return self.root.get(key, default)

class Config(object):

    def __init__(self, special_term='yay'):
        self.special_term = special_term
        self.openers = Openers()
        self.tt = TreeTransformer()

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
        self.tt.update(config)

    def clear(self):
        self.tt.root = None

    def get(self):
        return Resolver(self.tt.root.resolve()).resolve()

def load_uri(uri, special_term='yay'):
    c = Config(special_term)
    c.load_uri(uri)
    return c.get()

def load(stream, special_term='yay'):
    c = Config(special_term)
    c.load(stream)
    return c.get()

