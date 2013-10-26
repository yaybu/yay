# Copyright 2013 Isotoma Limited
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

from __future__ import absolute_import

import operator
import re
import functools
import inspect

from yay import errors
from yay.compat import io
from yay.openers import Openers
from yay.errors import merge_anchors as ma
from yay.compat import basestring

from itertools import chain

"""
The ``yay.ast`` module contains the classes that make up the graph.
"""


_DEFAULT = object()


class cached(object):

    def __init__(self, func):
        self.func = func

    def __call__(descriptor, self):
        if not hasattr(self, "cache"):
            self.cache = None
        if not self.cache:
            can_cache, result = descriptor.func(self)
            if not can_cache:
                return result
            self.cache = result
        return self.cache

    def __repr__(self):
        return self.func.__doc__

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)


class AST(object):

    lineno = 0
    _predecessor = None
    _resolving = False
    _expanding = False
    _get_context_checks_predecessors = False

    def __init__(self):
        self.subscribers = []

    def as_bool(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expected boolean", anchor=ma(anchor, self.anchor))

    def as_int(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expected integer", anchor=ma(anchor, self.anchor))

    def as_float(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expected float", anchor=ma(anchor, self.anchor))

    def as_number(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expected integer or float", anchor=ma(anchor, self.anchor))

    def as_safe_string(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expected string", anchor=ma(anchor, self.anchor))

    def as_string(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expected string", anchor=ma(anchor, self.anchor))

    def as_list(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expecting list", anchor=ma(anchor, self.anchor))

    def as_iterable(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expecting iterable", anchor=ma(anchor, self.anchor))

    def as_dict(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError(
            "Expecting dictionary", anchor=ma(anchor, self.anchor))

    def get_key(self, key, anchor=None):
        raise errors.TypeError(
            "Expecting dictionary or list", anchor=ma(anchor, self.anchor))

    def keys(self, anchor=None):
        raise errors.TypeError(
            "Expecting dictionary", anchor=ma(anchor, self.anchor))

    def get_iterable(self, anchor=None):
        raise errors.TypeError("Expected iterable", anchor=self.anchor)

    def construct(self, inner):
        raise errors.TypeError("Expected constructable", anchor=self.anchor)

    def get_type(self):
        raise errors.TypeError(
            "I don't know who I am, or what my destiny is", anchor=self.anchor)

    def as_digraph(self, visited=None):
        visited = visited or []
        if id(self) in visited:
            return
        visited.append(id(self))

        yield '%s [label="%s"];' % (id(self), self.__class__.__name__)
        # if self.parent:
        #    yield '%s -> %s [label="parent",style=dotted]' % (id(self), id(self.parent))
        #    for node in self.parent.as_digraph():
        #        yield node

        def _yield_graph(k, v):
            if isinstance(v, AST):
                yield '%s -> %s [label="%s"];' % (id(self), id(v), k)
                for line in v.as_digraph(visited):
                    yield line
            elif isinstance(v, list):
                for i, v in enumerate(v):
                    for line in _yield_graph("%s[%d]" % (k, i), v):
                        yield line
            elif isinstance(v, dict):
                for k2, v in v.items():
                    for line in _yield_graph("%s['%s']" % (k, k2), v):
                        yield line
            elif isinstance(v, (int, float, bool, basestring)):
                yield '%s -> %s [label="%s"];' % (id(self), id(v), k)
                yield '%s [label="%s"];' % (id(v), v)

        for k, v in self.__clone_vars().items():
            if k in ("anchor", ):
                continue
            for line in _yield_graph(k, v):
                yield line

        if self.predecessor and not isinstance(self.predecessor, NoPredecessorStandin):
            yield '%s -> %s [label="predecessor",style=dotted];' % (id(self), id(self.predecessor))
            for node in self.predecessor.as_digraph(visited):
                yield node

    def dynamic(self):
        """
        Does this graph member change over time?
        """
        return False

    def normalize_predecessors(self):
        """
        Forces inclusion of dependencies and ensures LazyPredecessor and UseMyPredecessorStandin nodes
        """

        for k, v in self.__clone_vars().items():
            if k in ("anchor", ):
                continue

            if isinstance(v, AST):
                v.normalize_predecessors()

            elif isinstance(v, list):
                for v2 in v:
                    if isinstance(v2, AST):
                        v2.normalize_predecessors()

            elif isinstance(v, dict):
                for v2 in v.values():
                    if isinstance(v2, AST):
                        v2.normalize_predecessors()

        obj = self
        while obj.predecessor and not isinstance(obj.predecessor, NoPredecessorStandin):
            if isinstance(obj.predecessor, (LazyPredecessor, UseMyPredecessorStandin)):
                try:
                    obj.predecessor = obj.predecessor.expand()
                except errors.NoPredecessor:
                    obj.predecessor = NoPredecessorStandin()
                    break

            obj = obj.predecessor

            obj.normalize_predecessors()

        return self

    def simplify(self):
        """
        Resolve any parts of the graph that are constant
        """
        return self

    def resolve(self):
        if self._resolving:
            raise errors.CycleError(
                "A cycle was detected in your configuration and processing cannot continue", anchor=self.anchor)
        self._resolving = True
        try:
            return self.resolve_once()
        finally:
            self._resolving = False

    def resolve_once(self):
        """
        Resolve an object into a simple type, like a string or a dictionary.

        Node does not provide an implementation of this, all subclasses should
        implemented it.
        """
        raise NotImplementedError(self.resolve)

    def expand(self):
        if self._expanding:
            raise errors.CycleError(
                "A cycle was detected in your configuration and processing cannot continue", anchor=self.anchor)
        self._expanding = True
        try:
            return self.expand_once()
        finally:
            self._expanding = False

    def expand_once(self):
        """
        Generate a simplification of this object that can replace it in the graph
        """
        return self

    def start_listening(self):
        """
        Subscribe to events from dependent nodes and any external monitoring sources
        """
        raise NotImplementedError(self.start_listening)

    def get_context(self, key):
        """
        Look up value of ``key`` and return it.

        This doesn't do any resolving, the return value will be a subclass of Node.
        """
        raise errors.NoMatching("Could not find '%s'" % key)

    @property
    def predecessor(self):
        return self._predecessor

    @predecessor.setter
    def predecessor(self, value):
        if self._predecessor:
            self._predecessor.successor = None
        self._predecessor = value
        if value:
            value.successor = self

    @property
    def head(self):
        """ Walks successors (the weak-ref reverse of predecessors) to find the most recent node """
        n = self
        while getattr(n, 'successor', None):
            n = n.successor
        return n

    @property
    def root(self):
        """
        Find and return the root of this document.
        """
        return self.parent.root

    def clone(self):
        """
        Return a copy of this node.
        """
        mapping = {}

        def _clone(parent, v):
            if id(v) in mapping:
                return mapping[id(v)]

            if isinstance(v, AST):
                child = v.__class__.__new__(v.__class__)
                mapping[id(v)] = child

                for k, v in v.__clone_vars().items():
                    child.__dict__[k] = _clone(child, v)
                if parent:
                    child.parent = parent
            elif isinstance(v, list):
                child = []
                mapping[id(v)] = child

                for inner in v:
                    child.append(_clone(parent, inner))
            elif isinstance(v, dict):
                child = {}
                mapping[id(v)] = child

                for k, inner in v.items():
                    child[k] = _clone(parent, inner)

            else:
                child = v

            return child

        return _clone(None, self)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__repr_vars())

    def __clone_vars(self):
        d = self.__dict__.copy()
        for var in ('parent', 'successor'):
            if var in d:
                del d[var]
        return d

    def __repr_vars(self):
        d = self.__dict__.copy()
        for var in ('anchor', 'parent', '_predecessor',
                    'successor', 'subscribers', '_ordered_keys',
                    '_iterator', '_position', '_buffer', '_dict'):
            if var in d:
                del d[var]
        return d

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__repr_vars() == other.__repr_vars()

    def get_local_labels(self):
        labels = set()
        if "labels" in self.__dict__:
            labels.update(self.__dict__['labels'])
        return labels

    def get_labels(self):
        root = self.root
        cur = self
        labels = set()
        while cur != root:
            labels.update(cur.get_local_labels())
            cur = cur.parent
        labels.update(root.get_local_labels())
        return labels

    def is_secret(self):
        return "secret" in self.get_labels()

    def contains_secrets(self):
        return self.is_secret()

    def subscribe(self, cbl):
        self.subscribers.append(cbl)

    def changed(self):
        for subscriber in self.subscribers:
            subscriber()


class Scalarish(object):

    """
    A mixin for an object that is a number, string or boolean

    By default if a casting error occurs an errors.ValueError will be raised
    that blames the current node. By passing in the optional ``anchor`` node
    you can blame the node that is consuming this node. For example::

        a: foo
        b: 5
        c: {{ a - b }}

    The most useful error here is to blame the identifier ``a`` inside the
    ``{{ brackets }}`` rather than to actually blame the scalar itself.

    A scalar cannot be treated as a stream.
    """

    def as_bool(self, default=_DEFAULT, anchor=None):
        try:
            return bool(self.resolve())
        except ValueError:
            raise errors.TypeError(
                "Expected bool", anchor=ma(anchor, self.anchor))

    def as_int(self, default=_DEFAULT, anchor=None):
        try:
            return int(self.resolve())
        except ValueError:
            raise errors.TypeError(
                "Expected integer", anchor=ma(anchor, self.anchor))

    def as_float(self, default=_DEFAULT, anchor=None):
        try:
            return float(self.resolve())
        except ValueError:
            raise errors.TypeError(
                "Expected float", anchor=ma(anchor, self.anchor))

    def as_number(self, default=_DEFAULT, anchor=None):
        """
        This will return an integer, and if it can't return an integer it
        will return a float. Otherwise it will fail with a TypeError.
        """
        resolved = self.resolve()

        if isinstance(resolved, (int, float)):
            return resolved

        try:
            return int(resolved)
        except ValueError:
            try:
                return float(resolved)
            except ValueError:
                raise errors.TypeError(
                    "Expected integer or float", anchor=ma(anchor, self.anchor))

    def as_safe_string(self, default=_DEFAULT, anchor=None):
        """ Returns a string that might includes obfuscation where secrets are used """
        parts = []

        if "secret" in self.parent.get_labels():
            return "*****"

        try:
            for part in self.get_string_parts():
                if "secret" in part.get_local_labels():
                    parts.append("*****")
                else:
                    parts.append(part.as_string())
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise
        return ''.join(parts)

    def as_string(self, default=_DEFAULT, anchor=None):
        resolved = self.resolve()
        if isinstance(resolved, (int, float, bool)):
            resolved = str(resolved)
        if not isinstance(resolved, basestring):
            raise errors.TypeError(
                "Expected string", anchor=ma(anchor, self.anchor))
        return resolved

    def get_string_parts(self):
        yield self

    def get_type(self):
        return "scalarish"


class Streamish(object):

    """
    A mixin for a class that behaves like a stream - i.e. is iterable

    This includes a default get implementation that gently unwinds
    generators and iterators
    """

    def __init__(self):
        super(Streamish, self).__init__()
        self._buffer = []
        self._position = 0
        self._iterator = None

    def _get_source_iterator(self):
        """
        Subclasses must implement this to allow the Streamish methods to buffer
        the expanded stream
        """
        raise NotImplementedError(self._get_source_iterator)

    def as_list(self, default=_DEFAULT, anchor=None):
        return list(self.as_iterable(default, anchor))

    def as_iterable(self, default=_DEFAULT, anchor=None):
        generator = self.get_iterable(anchor=ma(anchor, self.anchor))
        for val in generator:
            yield val.resolve()

    def get_iterable(self, anchor=None):
        idx = 0
        while True:
            self._fill_to(idx)
            yield self._buffer[idx]
            idx += 1

    def _fill_to(self, index):
        if not self._iterator:
            self._iterator = self._get_source_iterator()

        while len(self._buffer) < index + 1:
            self._buffer.append(next(self._iterator))

    def get_key(self, index):
        try:
            index = int(index)
        except ValueError:
            raise errors.TypeError(
                "Expected an integer, '%s' is not an integer" % index, anchor=self.anchor)

        self._fill_to(index)
        return self._buffer[index]

    def get_type(self):
        return "streamish"

    def resolve_once(self):
        return [x.resolve() for x in self.get_iterable()]

    def contains_secrets(self):
        for node in self.get_iterable():
            if node.contains_secrets():
                return True
        return self.is_secret()

    def start_listening(self):
        for child in self.get_iterable():
            child.start_listening()
            child.subscribe(self.changed)


class Dictish(object):

    def get_iterable(self, anchor=None):
        for key in self.keys(ma(anchor, self.anchor)):
            s = YayScalar(key)
            s.parent = self
            yield s

    def as_dict(self, default=_DEFAULT, anchor=None):
        return self.resolve()

    def get_type(self):
        return "dictish"

    def resolve_once(self):
        return dict((key, self.get_key(key).resolve()) for key in self.keys())

    def contains_secrets(self):
        for key in self.keys():
            if self.get_key(key).contains_secrets():
                return True
        return self.is_secret()

    def start_listening(self):
        for key in self.keys():
            c = self.get_key(key)
            c.start_listening()
            c.subscribe(self.changed)


class Proxy(object):

    """
    A mixin that forwards requested on to an expanded form

    A lot of objects in the tree don't actually contain data but are actually
    some sort of deferred lookup. For example::

        a: 55
        b: {{ a }}

    Here, the ``{{ a }}`` expression contains a reference to the real ``a``
    key. So any node that access ``b`` needs to proxy to the real ``a``.

    This mixin proxies all the standard interface methods to the node
    returned by ``self.expand()``.
    """

    def as_bool(self, default=_DEFAULT, anchor=None):
        try:
            return (
                self.expand().as_bool(default, anchor=ma(anchor, self.anchor))
            )
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_int(self, default=_DEFAULT, anchor=None):
        try:
            return (
                self.expand().as_int(default, anchor=ma(anchor, self.anchor))
            )
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_float(self, default=_DEFAULT, anchor=None):
        try:
            return (
                self.expand().as_float(default, anchor=ma(anchor, self.anchor))
            )
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_number(self, default=_DEFAULT, anchor=None):
        try:
            return (
                self.expand().as_number(
                    default, anchor=ma(anchor, self.anchor))
            )
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_safe_string(self, default=_DEFAULT, anchor=None):
        try:
            return (
                self.expand().as_safe_string(
                    default, anchor=ma(anchor, self.anchor))
            )
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_string(self, default=_DEFAULT, anchor=None):
        try:
            return (
                self.expand().as_string(
                    default, anchor=ma(anchor, self.anchor))
            )
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_list(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_list(default, ma(anchor, self.anchor))
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_iterable(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_iterable(default, ma(anchor, self.anchor))
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_dict(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_dict(ma(anchor, self.anchor))
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def keys(self, anchor=None):
        return self.expand().keys(ma(anchor, self.anchor))

    def get_string_parts(self):
        yield self

    def get_iterable(self, anchor=None):
        return self.expand().get_iterable(ma(anchor, self.anchor))

    def get_key(self, key):
        return self.expand().get_key(key)

    def construct(self, inner):
        return self.expand().construct(inner)

    def get_type(self):
        return self.expand().get_type()

    def get_local_labels(self):
        labels = super(Proxy, self).get_local_labels()
        try:
            expanded = self.expand()
            if expanded != self:
                labels.update(expanded.get_local_labels())
        except errors.NoPredecessor:
            pass
        return labels

    def expand_once(self):
        raise NotImplementedError(
            "%r does not implement expand or expand_once - but proxy types must" % type(self))

    def resolve_once(self):
        return self.expand().resolve()

    def contains_secrets(self):
        return self.expand().contains_secrets()

    def is_secret(self):
        return self.expand().is_secret()

    def start_listening(self):
        # FIXME: It is quite likely (certain, in fact) that we won't be able to
        # rely on expand here - e.g. an expand on an if with a dynamic guard
        # condition wouldn't work here!
        expanded = self.expand()
        expanded.start_listening()
        expanded.subscribe(self.changed)


class Tripwire(Proxy, AST):

    _get_context_checks_predecessors = True

    def __init__(self, node, expression, expected):
        super(Tripwire, self).__init__()
        self.node = node
        self.expression = expression
        self.expected = expected
        self.expanding = False

    def get_context(self, key):
        p = self.node

        while p and not isinstance(p, (NoPredecessorStandin, )):
            try:
                return p.get_context(key)
            except errors.NoMatching:
                if p._get_context_checks_predecessors:
                    break
            p = p.predecessor

        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def expand(self):
        if not self.expanding:
            self.expanding = True
            current = self.expression()
            if current != self.expected:
                raise errors.ParadoxError(
                    "Inconsistent configuration detected - changed from %r to %r" % (self.expected, current), anchor=self.anchor)
            self.expanding = False
        return self.node


class Pythonic(object):

    def __int__(self):
        return self.as_int()

    def __long__(self):
        return self.as_int()

    def __float__(self):
        return self.as_float()

    def __str__(self):
        return self.as_string()

    def __dir__(self):
        return list(self.keys())

    def __getattr__(self, key):
        ref = AttributeRef(self, key)
        ref.anchor = None
        ref.parent = self
        p = PythonicWrapper(ref)
        return p

    def __getitem__(self, key):
        if isinstance(key, slice):
            ref = SliceyThing(self, key)
        else:
            ref = Subscription(self, YayScalar(key))
        ref.anchor = None
        ref.parent = self
        return PythonicWrapper(ref)

    def __iter__(self):
        for val in self.get_iterable():
            p = PythonicWrapper(val)
            yield p


class PythonicWrapper(Pythonic, Proxy, AST):

    def __init__(self, inner):
        super(PythonicWrapper, self).__init__()
        self.inner = inner

    @property
    def parent(self):
        return self.inner.parent

    @parent.setter
    def parent(self, val):
        pass

    def expand_once(self):
        return self.inner.expand()

    def get_labels(self):
        return self.expand().get_labels()

    def start_listening(self):
        self.inner.start_listening()

    def subscribe(self, cbl):
        self.inner.subscribe(cbl)

    def get_path(self):
        if not hasattr(self, "parent"):
            return "<unparented>"
        elif isinstance(self.parent, Root):
            path = "<root>"
        elif isinstance(self.parent, PythonicWrapper):
            path = self.parent.get_path()
        else:
            path = "<unknown>"

        if isinstance(self.inner, AttributeRef):
            return path + "/" + self.inner.identifier
        elif isinstance(self.inner, Subscription):
            return path + "[%r]" % self.inner.expression_list[0].value

        return "<unknown>"

    def __repr__(self):
        return self.get_path()


class Root(Pythonic, Proxy, AST):

    """ The root of the document
    FIXME: This needs thinking about some more
    """

    _get_context_checks_predecessors = True

    def __init__(self, node=None):
        super(Root, self).__init__()
        self.openers = Openers(searchpath=[])
        self.node = NoPredecessorStandin()
        if node:
            node.predecessor = self.node
            self.node = node
            node.parent = self
        else:
            self.node = NoPredecessorStandin()
            self.node.parent = self

    def as_digraph(self, visited=None):
        visited = visited or []
        yield "digraph ast {"
        for line in self.node.as_digraph(visited):
            yield line
        yield "}"

    @property
    def root(self):
        return self

    def get_context(self, key):
        p = self.node
        while p and not isinstance(p, NoPredecessorStandin):
            try:
                return p.get_context(key)
            except errors.NoMatching:
                if p._get_context_checks_predecessors:
                    break

            p = p.predecessor

        try:
            return self.node.get_key(key)
        except KeyError:
            raise errors.NoMatching(
                "Key not found '%s'" % key, anchor=self.anchor)

    def expand(self):
        return self.node.expand()

    def get_local_labels(self):
        return ()

    def load_uri(self, uri):
        fp = self.openers.open(uri)
        return self.load(fp, uri, getattr(fp, "labels", ()))

    def loads(self, data, name="<Unknown>", labels=()):
        return self.load(io.StringIO(data), name, labels)

    def load(self, stream, name="<Unknown>", labels=()):
        node = self._parse(stream, name, labels)
        mda = node
        while mda.predecessor and not isinstance(mda.predecessor, NoPredecessorStandin):
            mda = mda.predecessor
        mda.predecessor = self.node
        self.node = node
        return node

    def _parse_uri(self, uri):
        fp = self.openers.open(uri)
        return self._parse(fp, uri, getattr(fp, "labels", ()))

    def _parse(self, stream, name="<Unknown>", labels=()):
        from yay import parser
        p = parser.Parser()
        data = stream.read()
        if hasattr(data, "decode"):
            data = data.decode("utf-8")
        node = p.parse(data, source=name)
        node.parent = self
        node.labels = labels
        return node


class Identifier(Proxy, AST):

    def __init__(self, identifier):
        super(Identifier, self).__init__()
        self.identifier = identifier

    def expand_once(self):
        __context__ = "Looking up '%s' in current scope" % self.identifier
        node = self.head
        root = self.root
        while node != root:
            try:
                return node.get_context(self.identifier).expand()
            except errors.NoPredecessor:
                pass
            except errors.NoMatching:
                pass
            except errors.NoMoreContext:
                # We are at the root of a Subgraph and shouldn't traverse
                # further.
                raise errors.NoMatching(
                    "Could not find '%s'" % self.identifier)
            node = node.parent

        assert node == root

        try:
            return node.get_context(self.identifier).expand()
        except errors.NoMatching:
            pass
        except errors.NoPredecessor:
            pass

        raise errors.NoMatching("Could not find '%s'" %
                                self.identifier, anchor=self.anchor)

    def get_local_labels(self):
        return self.expand().get_labels()

    def get_string_parts(self):
        yield self


class Literal(Scalarish, AST):

    def __init__(self, literal):
        super(Literal, self).__init__()
        self.literal = literal

    def resolve_once(self):
        return self.literal

    def start_listening(self):
        pass


class ParentForm(Scalarish, AST):
    # FIXME: Understand this better...

    def __init__(self, expression_list=None):
        super(ParentForm, self).__init__()
        self.expression_list = expression_list
        if expression_list:
            expression_list.parent = self

    def resolve_once(self):
        if not self.expression_list:
            return []
        return self.expression_list.resolve()


class UnaryExpr(Scalarish, AST):

    def __init__(self, inner):
        super(UnaryExpr, self).__init__()
        self.inner = inner
        inner.parent = self

    def dynamic(self):
        return self.inner.dynamic()

    @cached
    def simplify(self):
        if not self.dynamic():
            return True, Literal(self.resolve())
        else:
            return True, self.__class__(self.inner.simplify())

    def resolve_once(self):
        return self.op(self.inner.as_number())

    def get_local_labels(self):
        labels = super(UnaryEpr, self).get_local_labels()
        labels.update(self.inner.get_local_labels())
        return labels

    def start_listening(self):
        self.inner.start_listening()
        self.inner.subscribe(self.changed)


class UnaryMinus(UnaryExpr):

    """ The unary - (minus) operator yields the negation of its numeric
    argument. """

    op = operator.neg


class Invert(UnaryExpr):

    """ The unary ~ (invert) operator yields the bitwise inversion of its
    plain or long integer argument. The bitwise inversion of x is defined as
    -(x+1). It only applies to integral numbers. """

    op = operator.invert


class Not(UnaryExpr):
    op = operator.not_


class Expr(Scalarish, AST):

    """
    The ``Expr`` nodes tests for equality between a left and a right child. The
    result is either True or False.

    Tree reduction rules
    --------------------

    If both children are constant then this node can be reduced to a
    ``Literal``

    Otherwise, an equivalent expression node is returned that has had its children
    simplified.
    """

    def __init__(self, lhs, rhs):
        super(Expr, self).__init__()
        self.lhs = lhs
        lhs.parent = self
        self.rhs = rhs
        rhs.parent = self

    def dynamic(self):
        for c in (self.lhs, self.rhs):
            if c.dynamic():
                return True
        return False

    @cached
    def simplify(self):
        if not self.dynamic():
            return True, Literal(self.resolve())
        else:
            return (
                True, self.__class__(self.lhs.simplify(), self.rhs.simplify())
            )

    def resolve_once(self):
        return self.op(self.lhs.as_number(), self.rhs.as_number())

    def get_local_labels(self):
        labels = super(Expr, self).get_local_labels()
        labels.update(self.lhs.get_local_labels())
        labels.update(self.rhs.get_local_labels())
        return labels

    def start_listening(self):
        self.lhs.start_listening()
        self.lhs.subscribe(self.changed)
        self.rhs.start_listening()
        self.rhs.subscribe(self.changed)


class Equal(Expr):

    def resolve_once(self):
        return self.lhs.resolve() == self.rhs.resolve()


class NotEqual(Expr):

    def resolve_once(self):
        return self.lhs.resolve() != self.rhs.resolve()


class LessThan(Expr):
    op = operator.lt


class GreaterThan(Expr):
    op = operator.gt


class LessThanEqual(Expr):
    op = operator.le


class GreaterThanEqual(Expr):
    op = operator.ge


class Add(Expr):
    op = operator.add

    def resolve_once(self):
        try:
            return self.op(self.lhs.as_number(), self.rhs.as_number())
        except errors.TypeError:
            return self.op(self.lhs.as_string(), self.rhs.as_string())


class YayMerged(Expr):

    """ Combined scalars and templates """

    @classmethod
    def merge(klass, *items):
        """ This will return an AST node of the appropriate
        simplest type. We flatten our tree of merges, if we have one, then
        remerge everything, carefully appending strings in scalars whenever
        we can. This helps ensure that multiline blocks get wrapped properly.
        """
        def unwrap(v):
            if isinstance(v, YayMerged):
                for i in unwrap(v.lhs):
                    yield i
                for i in unwrap(v.rhs):
                    yield i
            else:
                yield v

        m = []
        for i in items:
            for j in unwrap(i):
                if len(m) > 0 and isinstance(j, YayScalar) \
                   and isinstance(m[-1], YayScalar):
                    m[-1].value = m[-1].value + j.value
                else:
                    m.append(j)
        if len(m) == 1:
            v = m[0]
        else:
            v = YayMerged(m[0], m[1])
            for i in m[2:]:
                v = YayMerged(v, i)
        return v

    def resolve_once(self):
        return self.lhs.as_string() + self.rhs.as_string()

    def get_string_parts(self):
        for part in self.lhs.get_string_parts():
            yield part
        for part in self.rhs.get_string_parts():
            yield part


class Subtract(Expr):
    op = operator.sub


class Multiply(Expr):
    op = operator.mul


class Divide(Expr):

    def op(self, lhs, rhs):
        try:
            return operator.truediv(lhs, rhs)
        except ZeroDivisionError:
            raise errors.ZeroDivisionError(
                "%s / %s - divide by zero is invalid" % (lhs, rhs), anchor=self.rhs.anchor)


class FloorDivide(Expr):

    def op(self, lhs, rhs):
        try:
            return operator.floordiv(lhs, rhs)
        except ZeroDivisionError:
            raise errors.ZeroDivisionError(
                "%s // %s - divide by zero is invalid" % (lhs, rhs), anchor=self.rhs.anchor)


class Mod(Expr):
    op = operator.mod


class Lshift(Expr):
    op = operator.lshift


class Rshift(Expr):
    op = operator.rshift


class Xor(Expr):
    op = operator.xor


class BitwiseOr(Expr):
    op = operator.or_


class Or(Expr):
    op = lambda self, lhs, rhs: lhs or rhs


class Else(Proxy, AST):

    def __init__(self, lhs, rhs):
        super(Else, self).__init__()
        self.lhs = lhs
        lhs.parent = self
        self.rhs = rhs
        rhs.parent = self

    def dynamic(self):
        for c in (self.lhs, self.rhs):
            if c.dynamic():
                return True
        return False

    def expand(self):
        try:
            return self.lhs.expand()
        except errors.NoMatching:
            return self.rhs.expand()


class BitwiseAnd(Expr):
    op = operator.and_


class And(Expr):

    """
    An ``And`` expression behaves much like the ``and`` keyword in python.

    Tree reduction rules
    --------------------

    If both parts of the expression are constant then the expression can be
    reduced to a Literal.

    If only one part is constant then it is tested to see if it is False.
    If so, the entire expression is simplified to ``Literal(False)``. If it is
    ``True`` then the ``And`` expression is reduced to the dynamic part of the
    expression.

    If both parts are dynamic then the And cannot be reduced. (However, a new
    And is returned that has its contents reduced).
    """

    op = lambda self, lhs, rhs: lhs and rhs

    def simplify(self):
        if self.lhs.dynamic():
            if self.rhs.dynamic():
                return And(self.lhs.simplify(), self.rhs.simplify())
            elif self.rhs.resolve():
                return self.lhs.simplify()
            else:
                return Literal(False)

        elif self.rhs.dynamic():
            if self.lhs.resolve():
                return self.rhs.simplify()
            else:
                return Literal(False)

        return Literal(self.resolve())


class NotIn(Expr):

    def resolve_once(self):
        return self.lhs.resolve() not in self.rhs.resolve()


class Power(Expr):
    op = operator.pow


class ConditionalExpression(Proxy, AST):

    def __init__(self, or_test, if_clause, else_clause):
        super(ConditionalExpression, self).__init__()
        self.or_test = or_test
        or_test.parent = self
        self.if_clause = if_clause
        if_clause.parent = self
        self.else_clause = else_clause
        else_clause.parent = self

    def expand_once(self):
        if self.or_test.resolve():
            return self.if_clause.expand()
        else:
            return self.else_clause.expand()


class ListDisplay(Proxy, AST):

    def __init__(self, expression_list=None):
        super(ListDisplay, self).__init__()
        self.expression_list = expression_list
        if expression_list:
            expression_list.parent = self

    def expand_once(self):
        if not self.expression_list:
            lst = YayList()
            lst.parent = self
            lst.anchor = self.anchor
            return lst
        return self.expression_list.expand()


class DictDisplay(Dictish, AST):

    def __init__(self, key_datum_list=None):
        super(DictDisplay, self).__init__()
        self.key_datum_list = key_datum_list
        self._dict = None
        self._ordered_keys = None

    def _refresh_self(self):
        self._dict = {}
        self._ordered_keys = []

        if self.key_datum_list:
            for kv in self.key_datum_list.key_data:
                key = kv.key.resolve()
                self._dict[key] = kv.value
                self._ordered_keys.append(key)

    def get_key(self, key):
        if not self._dict:
            self._refresh_self()
        return self._dict[key]

    def keys(self):
        if not self._dict:
            self._refresh_self()
        return self._ordered_keys


class KeyDatumList(AST):

    def __init__(self, *key_data):
        super(KeyDatumList, self).__init__()
        self.key_data = list(key_data)

    def append(self, key_datum):
        self.key_data.append(key_datum)


class KeyDatum(AST):

    def __init__(self, key, value):
        super(KeyDatum, self).__init__()
        self.key = key
        self.value = value


class AttributeRef(Proxy, AST):

    def __init__(self, primary, identifier):
        super(AttributeRef, self).__init__()
        self.primary = primary
        primary.parent = self
        self.identifier = identifier

    def expand_once(self):
        __context__ = " -> Looking up subkey '%s'" % self.identifier
        try:
            return self.primary.expand().get_key(self.identifier).expand()
        except KeyError:
            raise errors.NoMatching(
                "Could not find '%s'" % self.identifier, anchor=self.anchor)

    def get_local_labels(self):
        return self.expand().get_labels()

    def get_string_parts(self):
        yield self


class LazyPredecessor(Proxy, AST):

    def __init__(self, node, identifier):
        super(LazyPredecessor, self).__init__()
        # This is a sideways reference! No parenting...
        self.node = node
        self.identifier = identifier

    @property
    def anchor(self):
        return self.expand().anchor

    def get_key(self, key):
        try:
            predecessor = self.expand()
        except errors.NoPredecessor:
            raise KeyError(key)
        return predecessor.get_key(key)

    @cached
    def expand_once(self):
        if self.node.predecessor:
            parent_pred = self.node.predecessor.expand()
            try:
                pred = parent_pred.get_key(self.identifier)
            except KeyError:
                raise errors.NoPredecessor
            return True, pred.expand()
        raise errors.NoPredecessor


class UseMyPredecessorStandin(Proxy, AST):
    anchor = None

    def __init__(self, node):
        super(UseMyPredecessorStandin, self).__init__()
        # This is a sideways reference! No parenting...
        self.node = node

    @property
    def predecessor(self):
        return self.node.predecessor

    def get_key(self, key):
        try:
            return self.expand().get_key(key)
        except errors.NoPredecessor:
            raise KeyError(key)

    def expand_once(self):
        return self.node.predecessor.expand()


class NoPredecessorStandin(Proxy, AST):

    predecessor = None

    def expand(self):
        raise errors.NoPredecessor("Node has no predecessor")

    def start_listening(self):
        pass


class Subscription(Proxy, AST):

    def __init__(self, primary, *expression_list):
        super(Subscription, self).__init__()
        self.primary = primary
        primary.parent = self
        self.expression_list = list(expression_list)
        if len(self.expression_list) > 1:
            raise errors.SyntaxError(
                "Keys must be scalars, not tuples", anchor=self.anchor)
        for e in self.expression_list:
            e.parent = self

    def expand_once(self):
        key = self.expression_list[0].resolve()
        try:
            return self.primary.expand().get_key(key).expand()
        except KeyError:
            raise errors.NoMatching(
                "Could not find '%s'" % key, anchor=self.anchor)


class SimpleSlicing(Streamish, AST):

    """
    Implements simple slices of any ``AST`` type that implements the
    ``Streamish`` interface.

    Because of the default methods provided by the ``Streamish`` mixin this
    class only needs to implement ``_get_source_iterator``. This yields objects that
    match the specified stride.
    """

    def __init__(self, primary, short_slice):
        super(SimpleSlicing, self).__init__()
        self.primary = primary
        primary.parent = self
        self.short_slice = short_slice
        short_slice.parent = self

    def _get_source_iterator(self, anchor=None):
        lower_bound = self.short_slice.lower_bound.resolve()
        upper_bound = self.short_slice.upper_bound.resolve()
        stride = self.short_slice.stride.resolve()

        for i in range(lower_bound, upper_bound, stride):
            yield self.primary.expand().get_key(i)


class Slice(AST):

    def __init__(self, lower_bound=None, upper_bound=None, stride=None):
        super(Slice, self).__init__()
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.stride = stride or YayScalar(1)

import re


class Call(Proxy, AST):

    def __init__(self, primary, args=None, kwargs=None):
        super(Call, self).__init__()
        self.primary = primary
        primary.parent = self
        self.args = args
        if self.args:
            for arg in self.args:
                arg.parent = self
        self.kwargs = kwargs

    def expand_once(self):
        args = []
        if self.args:
            for arg in self.args:
                args.append(arg.clone())

        kwargs = {}
        if self.kwargs:
            for kwarg in self.kwargs.kwargs:
                k = kwargs[
                    kwarg.identifier.identifier] = kwarg.expression.clone()

        try:
            macro = self.primary.expand()
            call = CallDirective(self.primary, None)
            node = Context(call, kwargs)
            node.anchor = self.anchor
        except errors.NoMatching:
            call = node = CallCallable(self.primary, args, kwargs)

        call.anchor = self.anchor
        node.parent = self

        return node


class CallCallable(Proxy, AST):

    allowed = {
        "range": range,
        "replace": lambda i, r, w: i.replace(r, w),
        "sub": re.sub,
    }

    def __init__(self, primary, args=None, kwargs=None):
        super(CallCallable, self).__init__()
        self.primary = primary
        if not self.primary.identifier in self.allowed:
            raise errors.NoMatching(
                "Could not find '%s'" % self.primary.identifier)

        self.args = args
        for a in args:
            a.parent = self

        self.kwargs = kwargs
        for k in kwargs:
            k.parent = self

    def expand_once(self):
        args = [x.resolve() for x in self.args]
        kwargs = dict((k, v.resolve()) for (k, v) in self.kwargs.items())
        result = self.allowed[self.primary.identifier](*args, **kwargs)
        bound = bind(result)
        bound.parent = self
        return bound


class ArgumentList(AST):

    def __init__(self, args, kwargs=None):
        super(ArgumentList, self).__init__()
        self.args = args
        self.kwargs = kwargs


class PositionalArguments(AST):

    def __init__(self, *expressions):
        super(PositionalArguments, self).__init__()
        self.args = list(expressions)

    def append(self, expression):
        self.args.append(expression)


class KeywordArguments(AST):

    def __init__(self, *keyword_items):
        super(KeywordArguments, self).__init__()
        self.kwargs = list(keyword_items)

    def append(self, keyword_item):
        self.kwargs.append(keyword_item)


class Kwarg(AST):

    def __init__(self, identifier, expression):
        super(Kwarg, self).__init__()
        self.identifier = identifier
        self.expression = expression


class TargetList(AST):

    def __init__(self, *targets):
        super(TargetList, self).__init__()
        self.v = list(targets)

    def append(self, target):
        self.v.append(target)


class ParameterList(AST):

    def __init__(self, *defparameters):
        super(ParameterList, self).__init__()
        self.parameter_list = list(defparameters)

    def append(self, defparameter):
        self.parameter_list.append(defparameter)


class DefParameter(AST):

    def __init__(self, parameter, expression=None):
        super(DefParameter, self).__init__()
        self.parameter = parameter
        self.expression = expression


class Sublist(AST):

    def __init__(self, *parameters):
        super(Sublist, self).__init__()
        self.sublist = list(parameters)

    def append(self, parameter):
        self.sublist.append(parameter)


class YayList(Streamish, AST):

    def __init__(self, *items):
        super(YayList, self).__init__()
        self.value = list(items)
        for x in self.value:
            x.parent = self

    def append(self, item):
        self.value.append(item)
        item.parent = self

    def get_key(self, idx):
        try:
            idx = int(idx)
        except ValueError:
            raise errors.TypeError("Expected integer", anchor=self.anchor)

        if idx < 0:
            raise errors.TypeError(
                "Index must be greater than 0", anchor=self.anchor)
        elif idx >= len(self.value):
            raise errors.TypeError("Index out of range", anchor=self.anchor)

        return self.value[idx]

    def get_iterable(self, anchor=None):
        return iter(self.value)


class ExpressionList(YayList):
    pass


class YayDict(Dictish, AST):

    """ A dictionary in yay may redefine items, so update merely appends. The
    value is a list of 2-tuples """

    def __init__(self, value=None):
        super(YayDict, self).__init__()
        self.values = {}
        self._ordered_keys = []
        if value:
            for (k, v) in value:
                self.update(k, v)

    def update(self, k, v):
        try:
            predecessor = self.get_key(k)
        except KeyError:
            predecessor = LazyPredecessor(self, k)

        v.parent = self
        self.values[k] = v

        if not k in self._ordered_keys:
            self._ordered_keys.append(k)

        # Respect any existing predecessors rather than blindly settings
        # v.predecessor
        while v.predecessor and not isinstance(v.predecessor, (NoPredecessorStandin, LazyPredecessor)):
            v = v.predecessor
            v.parent = self
        v.predecessor = predecessor

    def merge(self, other_dict):
        # This function should ONLY be called by parser and ONLY to merge 2
        # YayDict nodes...
        assert isinstance(other_dict, YayDict)
        for k in other_dict.keys():
            self.update(k, other_dict.get_key(k))

    def keys(self, anchor=None):
        seen = set()
        try:
            for key in self.predecessor.keys(anchor=ma(anchor, self.anchor)):
                seen.add(key)
                yield key
        except errors.NoPredecessor:
            pass
        for key in self._ordered_keys:
            if not key in seen:
                yield key

    def get_context(self, key):
        if key == "here":
            return self.head
        return super(YayDict, self).get_context(key)

    def get_key(self, key):
        if key in self.values:
            return self.values[key]
        try:
            return self.predecessor.expand().get_key(key)
        except errors.NoPredecessor:
            pass
        raise KeyError("Key '%s' not found" % key)


class YayExtend(Streamish, AST):

    def __init__(self, value):
        super(YayExtend, self).__init__()
        self.value = value
        value.parent = self

    def _get_source_iterator(self, anchor=None):
        try:
            for node in self.predecessor.get_iterable(ma(anchor, self.anchor)):
                yield node
        except errors.NoPredecessor:
            pass

        for node in self.value.get_iterable(ma(anchor, self.anchor)):
            yield node


class YayScalar(Scalarish, AST):

    def __init__(self, value):
        super(YayScalar, self).__init__()

        if isinstance(value, (int, float)):
            self.value = value
            return

        try:
            self.value = int(value)
        except ValueError:
            try:
                self.value = float(value)
            except ValueError:
                self.value = value

    def resolve_once(self):
        return self.value

    def start_listening(self):
        pass


class YayMultilineScalar(Scalarish, AST):

    chompers = {
        '>': "chomp_fold",
        '|': "chomp_literal",
        '|+': "chomp_keep",
        '|-': "chomp_strip",
    }

    def __init__(self, value, mtype):
        """ mtype is one of the chomper keys """

        super(YayMultilineScalar, self).__init__()
        self.__value = value
        self.mtype = mtype
        self.chomper = getattr(self, self.chompers[self.mtype])

    def append(self, value):
        if not value:
            return
        if isinstance(value, YayScalar) and not value.value:
            return
        if isinstance(value, basestring):
            value = YayScalar(value)
        if isinstance(value, YayScalar) and isinstance(self.__value, YayScalar):
            self.__value = YayScalar(self.__value.value + value.value)
        else:
            self.__value = YayMerged.merge(self.__value, value)

    @property
    def value(self):
        return self.to_scalar()

    def to_scalar(self):
        """ Return an appropriate representation with newlines handled. """
        s = self.chomp_ast(self.chomper, self.__value)
        if isinstance(s, YayScalar):
            s.value = s.value.rstrip(" ")
        if isinstance(s, YayMerged):
            if isinstance(s.rhs, YayScalar):
                s.rhs.value = s.rhs.value.rstrip(" ")
        return s

    @classmethod
    def chomp_ast(klass, method, item):
        if isinstance(item, basestring):
            return method(item)
        elif isinstance(item, YayMerged):
            return YayMerged(
                klass.chomp_ast(method, item.lhs),
                klass.chomp_ast(method, item.rhs),
            )
        elif isinstance(item, YayScalar):
            return YayScalar(method(item.value))
        else:
            # don't chomp this
            return item

    @staticmethod
    def chomp_fold(value):
        """
        For multiline strings introduced with only '>'.

        Folding allows long lines to be broken anywhere a single space
        character separates two non-space characters.
        """
        # Our implementation, and specification, is much simpler than YAMLs
        # which is uselessly complex. \n's are replaced with spaces, and
        # collapsed
        v = []
        for line in value.split("\n"):
            if line:
                v.append(line)
            else:
                v.append("")
        rv = " ".join(v)
        return rv

    @staticmethod
    def chomp_literal(value):
        """
        For multiline strings introduced with only '|'.

        In this case, the final line break character is preserved in the
        scalar's content. However, any trailing empty lines are excluded
        from the scalar's content.
        """
        return re.sub("[\n]+$", "\n", value)

    @staticmethod
    def chomp_keep(value):
        """
        For multiline strings introduced with '|+'.

        In this case, the final line break and any trailing empty lines are
        considered to be part of the scalar's content. These additional
        lines are not subject to folding.
        """
        return value

    @staticmethod
    def chomp_strip(value):
        """
        For multiline strings introduced with '|-'.

        In this case, the final line break and any trailing empty lines are
        excluded from the scalar's content.
        """

        return value.rstrip("\n")


class Stanzas(Proxy, AST):

    _get_context_checks_predecessors = True

    def __init__(self, *stanzas):
        super(Stanzas, self).__init__()
        self.value = UseMyPredecessorStandin(self)
        for s in stanzas:
            self.append(s)

    def append(self, stanza):
        stanza.predecessor = self.value or NoPredecessorStandin()
        stanza.parent = self
        self.value = stanza

    def get_context(self, key):
        p = self.value
        while p and not isinstance(p, (NoPredecessorStandin, )):
        # while p and p != self.predecessor:
            try:
                return p.get_context(key)
            except errors.NoMatching:
                if p._get_context_checks_predecessors:
                    break
            p = p.predecessor

        raise errors.NoMatching("Could not find '%s'" % key)

    def get_local_labels(self):
        labels = set()
        if "labels" in self.__dict__:
            labels.update(self.__dict__['labels'])
        return labels

    def get_type(self):
        return self.value.get_type()

    def expand(self):
        if self.get_type() == "streamish":
            i = StanzasIterator(self).expand()
            i.anchor = self.anchor
            i.parent = self
            return i
        return self.value.expand()


class StanzasIterator(Streamish, AST):

    def __init__(self, inner, follow_predecessor=True):
        super(StanzasIterator, self).__init__()
        self.inner = inner
        self.follow_predecessor = follow_predecessor

    def _get_source_iterator(self, anchor=None):
        stack = []
        cur = self.inner.value
        while not isinstance(cur, (UseMyPredecessorStandin, NoPredecessorStandin)):
            stack.insert(0, cur)
            cur = cur.predecessor
        stack.insert(0, cur)

        assert isinstance(stack[0], UseMyPredecessorStandin)

        if not self.follow_predecessor:
            stack.pop(0)

        while stack:
            try:
                first = stack.pop(0).expand()
                stack.insert(0, first)
            except errors.NoPredecessor:
                pass
            else:
                break

        for node in stack:
            try:
                for child in node.get_iterable():
                    yield child
            except errors.NoPredecessor:
                pass


class Directives(Proxy, AST):

    _get_context_checks_predecessors = True

    def __init__(self, *directives):
        super(Directives, self).__init__()
        self.value = UseMyPredecessorStandin(self)
        for d in directives:
            self.append(d)

    def append(self, directive):
        directive.parent = self
        directive.predecessor = self.value or NoPredecessorStandin()
        self.value = directive

    def get_context(self, key):
        p = self.value
        while p and p != self.predecessor:
            try:
                return p.get_context(key)
            except errors.NoMatching:
                if p._get_context_checks_predecessors:
                    break
            p = p.predecessor

        raise errors.NoMatching("Could not find '%s'" % key)

    def get_local_labels(self):
        labels = set()
        if "labels" in self.__dict__:
            labels.update(self.__dict__['labels'])
        return labels

    def get_type(self):
        return self.value.get_type()

    def expand(self):
        if self.get_type() == "streamish":
            i = StanzasIterator(self, False).expand()
            i.anchor = self.anchor
            i.parent = self
            return i
        return self.value.expand()


class Include(Proxy, AST):

    _get_context_checks_predecessors = True

    def __init__(self, expr):
        super(Include, self).__init__()
        self.expr = expr
        expr.parent = self
        self.detector = []
        self.expanding = False

    def get_context(self, key):
        try:
            expanded = self.expand()
        except errors.NoPredecessor:
            raise errors.NoMatching("Could not find '%s'" % key)

        p = expanded
        while p and not isinstance(p, (NoPredecessorStandin, )):
            try:
                return p.get_context(key)
            except errors.NoMatching:
                if p._get_context_checks_predecessors:
                    break
            p = p.predecessor

        raise errors.NoMatching("Could not find '%s'" % key)

    def get_key(self, key):
        if self.expanding:
            try:
                return self.predecessor.get_key(key)
            except errors.NoPredecessor:
                raise KeyError("No such key '%s'" % key)

        # if key in self.detector:
        #    raise KeyError("'%s' not found" % key)
        try:
            self.detector.append(key)
            return self.expand().get_key(key)
        finally:
            self.detector.remove(key)

    @cached
    def expand(self):
        if self.expanding:
            return False, self.predecessor

        self.expanding = True

        # Greedy lazyness at its finest
        # Parse predecessors first, otherwise their contributions to things
        # like the search path won't be considered.
        try:
            self.predecessor.expand()
        except errors.NoPredecessor:
            pass

        expr = self.expr.resolve()
        expanded = self.root._parse_uri(expr)

        self.expanding = False

        expanded.predecessor = UseMyPredecessorStandin(self)
        expanded.parent = self.parent

        t = Tripwire(expanded, self.expr.resolve, expr)
        t.parent = self.parent
        t.anchor = self.anchor

        return True, t


class Search(Proxy, AST):

    def __init__(self, expr):
        super(Search, self).__init__()
        self.expr = expr
        expr.parent = self

    def expand_once(self):
        return self.predecessor.expand()


class Set(Proxy, AST):

    def __init__(self, var, expr):
        super(Set, self).__init__()
        self.var = var
        var.parent = self

        self.expr = expr
        expr.parent = self

    def get_context(self, key):
        if key == self.var.identifier:
            return self.expr
        return super(Set, self).get_context(key)

    def expand_once(self):
        if self.predecessor.get_type() == "streamish":
            node = YayList()
            node.anchor = self.anchor
        else:
            node = self.predecessor.expand()
        return node


class If(Proxy, AST):

    """
    An If block has a guard condition. If that condition is True the
    result expression is returned. Otherwise the else_ expression is.

    Tree reduction rules
    --------------------

    If the guard condition is constant then the If expression can be
    simplified out of the graph.
    """

    def __init__(self, condition, on_true, on_false=None):
        super(If, self).__init__()
        self.condition = condition
        self.condition.parent = self

        self.on_true = on_true
        self.on_true.parent = self
        self.on_true.predecessor = UseMyPredecessorStandin(self)

        if on_false:
            self.on_false = on_false
            self.on_false.predecessor = UseMyPredecessorStandin(self)
            self.on_false.parent = self
        else:
            self.on_false = None

        self.passthrough_mode = False

    @cached
    def expand(self):
        if self.passthrough_mode:
            return False, self.predecessor.expand()

        self.passthrough_mode = True
        try:
            cond = self.condition.as_bool()
        finally:
            self.passthrough_mode = False

        if cond:
            node = self.on_true.expand()
        elif self.on_false:
            node = self.on_false.expand()
        else:
            if self.predecessor.get_type() == "streamish":
                node = YayList()
                node.anchor = self.anchor
            else:
                node = self.predecessor.expand()

        t = Tripwire(node, self.condition.as_bool, cond)
        t.anchor = self.anchor
        return True, t

    def add_elif(self, elif_):
        node = self
        while isinstance(node.on_false, If):
            node = node.on_false

        node.on_false = elif_
        elif_.parent = node

    def add_else(self, else_):
        node = self
        while isinstance(node.on_false, If):
            node = node.on_false

        node.on_false = else_
        else_.parent = node


class Select(Proxy, AST):

    def __init__(self, expr, cases):
        super(Select, self).__init__()
        self.expr = expr
        expr.parent = self
        self.cases = cases
        cases.parent = self
        self.expanding = False

    @cached
    def expand(self):
        if self.expanding:
            return False, self.predecessor

        self.expanding = True
        value = self.expr.as_string()
        self.expanding = False

        for case in self.cases.cases:
            if case.key == value:
                t = Tripwire(case.node.expand(), self.expr.as_string, value)
                t.anchor = self.anchor
                return True, t

        raise errors.NoMatching(
            "Select does not have key '%s'" % value, anchor=self.anchor)


class CaseList(AST):

    def __init__(self, *cases):
        super(CaseList, self).__init__()
        self.cases = []
        [self.append(c) for c in cases]

    def append(self, case):
        case.parent = self
        self.cases.append(case)


class Case(AST):

    def __init__(self, key, node):
        super(Case, self).__init__()
        self.key = key
        self.node = node
        node.parent = self


class Prototype(AST):

    def __init__(self, node):
        super(Prototype, self).__init__()
        self.node = node

    def construct(self, inner):
        return Stanzas(Self(), inner.clone(), self.node.clone())


class New(Proxy, AST):

    def __init__(self, target, node):
        super(New, self).__init__()
        self.target = target
        target.parent = self
        self.node = node

    @cached
    def expand(self):
        node = self.target.construct(self.node.clone())
        node.parent = self
        node.anchor = self.anchor

        # Resepct predecessors, don't overwrite them
        p = node
        while p.predecessor and not isinstance(p.predecessor, (NoPredecessorStandin, LazyPredecessor)):
            p = p.predecessor
            p.parent = self
        p.predecessor = UseMyPredecessorStandin(self)

        return True, node


class Ephemeral(Proxy, AST):

    def __init__(self, target, inner):
        super(Ephemeral, self).__init__()
        self.target = target
        self.inner = inner

    def get_context(self, key):
        if key == self.target.identifier:
            return self.inner
        raise errors.NoMatching("Could not find '%s'" % key)

    def expand_once(self):
        return self.predecessor.expand()


class Self(Proxy, AST):

    def get_context(self, key):
        if key == "self":
            return self.head
        raise errors.NoMatching("Could not find '%s'" % key)

    def expand_once(self):
        return self.predecessor.expand()


class Macro(AST):

    def __init__(self, node):
        super(Macro, self).__init__()
        self.node = node

    def call(self, params):
        pass


class CallDirective(Proxy, AST):

    def __init__(self, target, node):
        super(CallDirective, self).__init__()
        self.target = target
        target.parent = self
        self.node = node

    def expand_once(self):
        macro = self.target.expand()
        clone = macro.node.clone()
        if not self.node:
            clone.parent = self
            return clone.expand()
        context = Context(clone, self.node.expand().values)
        context.parent = self
        context.anchor = self.anchor
        return context.expand()


class For(Streamish, AST):

    def __init__(self, target, in_clause, node, if_clause=None):
        super(For, self).__init__()

        self.target = target
        target.parent = self
        self.if_clause = if_clause
        if if_clause:
            if_clause.parent = self
        self.in_clause = in_clause
        in_clause.parent = self
        self.node = node
        node.parent = self

    def _get_source_iterator(self, anchor=None):
        for item in self.in_clause.get_iterable(ma(anchor, self.anchor)):
            # self.target.identifier: This probably shouldn't be an identifier
            c = Context(self.node.clone(), {self.target.identifier: item})
            c.parent = self.parent
            c.anchor = self.anchor

            if self.if_clause:
                f = self.if_clause.clone()
                f.parent = c
                if not f.resolve():
                    continue

            for node in c.get_iterable(ma(anchor, self.anchor)):
                yield node


class Context(Proxy, AST):

    def __init__(self, value, context):
        super(Context, self).__init__()
        self.value = value
        self.value.parent = self

        # Context should not be reparented as we want things to be
        # evaluated in the original context.
        self.context = context

    def get_context(self, key):
        """
        If ``key`` is provided by this node return it, otherwise fall
        back to default implementation.
        """
        val = self.context.get(key, None)
        if not val:
            val = super(Context, self).get_context(key)
        return val

    def expand_once(self):
        return self.value.expand()


class ListComprehension(Streamish, AST):

    def __init__(self, expression, list_for):
        super(ListComprehension, self).__init__()
        self.expression = expression
        expression.parent = self
        self.list_for = list_for
        list_for.parent = self

    def _get_source_iterator(self, anchor=None):
        for node in self.list_for.expressions.get_iterable(ma(anchor, self.anchor)):
            ctx = Context(self.expression.clone(), {
                          self.list_for.targets.identifier: node})
            ctx.anchor = self.anchor
            ctx.parent = self
            yield ctx.expand()


class ListFor(Streamish, AST):

    def __init__(self, targets, expressions, iterator=None):
        super(ListFor, self).__init__()
        self.targets = targets
        targets.parent = self
        self.expressions = expressions
        expressions.parent = self
        self.iterator = iterator
        if iterator:
            iterator.parent = self


class ListIf(AST):

    def __init__(self, expression, iterator=None):
        super(ListIf, self).__init__()
        self.expression = expression
        self.iterator = iterator


class Comprehension(AST):

    def __init__(self, expression, comp_for):
        super(Comprehension, self).__init__()
        self.expression = expression
        self.comp_for = comp_for


class CompFor(AST):

    def __init__(self, targets, test, iterator=None):
        super(CompFor, self).__init__()
        self.targets = targets
        self.test = test
        self.iterator = iterator


class CompIf(AST):

    def __init__(self, expression, iterator=None):
        super(CompIf, self).__init__()
        self.expression = expression
        self.iterator = iterator


class GeneratorExpression(AST):

    def __init__(self, expression, comp_for):
        super(GeneratorExpression, self).__init__()
        self.expression = expression
        self.comp_for = comp_for


class DictComprehension(AST):

    def __init__(self, key, value, comp_for):
        super(DictComprehension, self).__init__()
        self.key = key
        self.value = value
        self.comp_for = comp_for


class SetDisplay(AST):

    def __init__(self, v):
        super(SetDisplay, self).__init__()
        self.v = v


class StringConversion(AST):

    def __init__(self, v):
        super(StringConversion, self).__init__()
        self.v = v


class LambdaForm(AST):

    def __init__(self, expression, params=None):
        super(LambdaForm, self).__init__()
        self.expression = expression
        self.params = params


class PythonClassFactory(AST):

    def __init__(self, inner):
        super(PythonClassFactory, self).__init__()
        self.inner = inner

    def construct(self, inner):
        if not issubclass(self.inner, PythonClass):
            raise errors.TypeError("'%s' is not usable from Yay" % classname)

        return self.inner(inner)


class PythonClassAttributes(Dictish, AST):

    def __init__(self):
        super(PythonClassAttributes, self).__init__()
        self.attributes = {}

    def set(self, key, value):
        if not key in self.attributes:
            attr = self.attributes[key] = YayScalar(value)
            attr.parent = self
            attr.changed()
        else:
            attr = self.attributes[key]
            if attr.value != value:
                attr.value = value
                attr.changed()

    def get_key(self, key):
        return self.attributes[key]

    def keys(self, anchor=None):
        for key in self.attributes.keys():
            yield key


class PythonClass(Proxy, AST):

    """
    This is a Mixin for writing nodes that can be created with the ``create`` syntax
    """

    def __init__(self, params):
        super(PythonClass, self).__init__()
        # Object to exposed metadata exported by this class to yay
        self.members = PythonClassAttributes()
        self.members.parent = self

        # Node containing metadata provided by the user
        params.parent = self
        params.predecessor = self.members
        params.parent = self

        self.params = PythonicWrapper(params)
        self.params.parent = self
        self.stale = True

    def apply(self):
        raise NotImplementedError(self.apply)

    def get_key(self, key):
        try:
            return self.params.get_key(key)
        except KeyError:
            if self.stale:
                self.apply()
                self.stale = False
            return self.members.get_key(key)

    def expand_once(self):
        if self.stale:
            self.apply()
            self.stale = False

        return self.params.expand()

    def get_local_labels(self):
        return AST.get_local_labels(self)

    def changed(self):
        self.apply()
        super(PythonClass, self).changed()

    def start_listening(self):
        super(PythonClass, self).start_listening()
        self.members.start_listening()
        self.members.subscribe(self.changed)


class PythonIterable(Streamish, AST):

    anchor = None

    def __init__(self, iterable):
        super(PythonIterable, self).__init__()
        self.iterable = iterable

    def _get_source_iterator(self, anchor=None):
        for node in self.iterable:
            obj = bind(node)
            obj.parent = self
            yield obj


class PythonDict(Dictish, AST):

    anchor = None

    def __init__(self, dict):
        super(PythonDict, self).__init__()
        self.dict = dict
        # FIXME: We should either have a fake anchor or generate one by
        # inspecting the frame
        self.anchor = None

    def get_key(self, key):
        try:
            obj = bind(self.dict[key])
            obj.parent = self
            obj.predecessor = LazyPredecessor(self, key)
            return obj
        except KeyError:
            pass

        try:
            return self.predecessor.get_key(key)
        except errors.NoPredecessor:
            pass

        raise KeyError("No key '%s'" % key)

    def keys(self, anchor=None):
        seen = set()
        try:
            for key in self.predecessor.keys(ma(anchor, self.anchor)):
                seen.add(key)
                yield key
        except errors.NoPredecessor:
            pass

        for key in sorted(self.dict.keys()):
            if key in seen:
                continue
            yield key


bindings = [
    (inspect.isgenerator,
     PythonIterable),
    (lambda v: isinstance(v, list),
     PythonIterable),
    (lambda v: isinstance(v, dict), PythonDict),
    (lambda v: isinstance(v, (int, float, basestring, bool)), YayScalar),
]

if inspect.isclass(range):
    bindings.append((lambda v: isinstance(v, range), PythonIterable))


def bind(v):
    for detector, wrapper in bindings:
        if detector(v):
            return wrapper(v)
    raise errors.TypeError(
        "Encountered unbindable object (type = %r)" % repr(v))


AST._predecessor = NoPredecessorStandin()
