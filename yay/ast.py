import operator
from . import errors
from .openers import Openers
import re
import functools
import inspect

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

    def as_bool(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError("Expected boolean", anchor=anchor or self.anchor)

    def as_int(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError("Expected integer", anchor=anchor or self.anchor)

    def as_float(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError("Expected float", anchor=anchor or self.anchor)

    def as_number(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError("Expected integer or float", anchor=anchor or self.anchor)

    def as_safe_string(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError("Expected string", anchor=anchor or self.anchor)

    def as_string(self, default=_DEFAULT, anchor=None):
        raise errors.TypeError("Expected string", anchor=anchor or self.anchor)

    def as_dict(self, anchor=None):
        raise errors.TypeError("Expecting dictionary", anchor=anchor or self.anchor)

    def keys(self, anchor=None):
        raise errors.TypeError("Expecting dictionary", anchor=anchor or self.anchor)

    def as_iterable(self, anchor=None):
        raise errors.TypeError("Expected iterable", anchor=self.anchor)

    def as_digraph(self, visited=None):
        visited = visited or []
        if id(self) in visited:
            return
        visited.append(id(self))

        yield '%s [label="%s"];' % (id(self), self.__class__.__name__)
        #if self.parent:
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
                    for line in _yield_graph("%s[%d]" % (k,i), v):
                        yield line
            elif isinstance(v, dict):
                for k2, v in v.items():
                    for line in _yield_graph("%s['%s']" % (k,k2), v):
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
            raise errors.CycleError("A cycle was detected in your configuration and processing cannot continue", anchor=self.anchor)
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
            raise errors.CycleError("A cycle was detected in your configuration and processing cannot continue", anchor=self.anchor)
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

        This boldly assumes the graph is acyclic.
        """
        def _clone(v):
            if isinstance(v, AST):
                child = v.clone()
                child.parent = instance
                return child
            elif isinstance(v, list):
                lst = []
                for child in v:
                    lst.append(_clone(child))
                return lst
            elif isinstance(v, dict):
                dct = {}
                for k, child in v.items():
                    dct[k] = _clone(child)
                return dct
            else:
                return v

        instance = self.__class__.__new__(self.__class__)
        for k, v in self.__clone_vars().items():
            instance.__dict__[k] = _clone(v)

        return instance

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__repr_vars())

    def __clone_vars(self):
        d = self.__dict__.copy()
        for var in ('parent', '_predecessor', 'successor'):
            if var in d:
                del d[var]
        return d

    def __repr_vars(self):
        d = self.__dict__.copy()
        for var in ('anchor', 'parent', '_predecessor', 'successor'):
            if var in d:
                del d[var]
        return d

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__repr_vars() == other.__repr_vars()


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
            raise errors.TypeError("Expected bool", anchor=anchor or self.anchor)

    def as_int(self, default=_DEFAULT, anchor=None):
        try:
            return int(self.resolve())
        except ValueError:
            raise errors.TypeError("Expected integer", anchor=anchor or self.anchor)

    def as_float(self, default=_DEFAULT, anchor=None):
        try:
            return float(self.resolve())
        except ValueError:
            raise errors.TypeError("Expected float", anchor=anchor or self.anchor)

    def as_number(self, default=_DEFAULT, anchor=None):
        """
        This will return an integer, and if it can't return an integer it
        will return a float. Otherwise it will fail with a TypeError.
        """
        resolved = self.resolve()
        try:
            return int(resolved)
        except ValueError:
            try:
                return float(resolved)
            except ValueError:
                raise errors.TypeError("Expected integer or float", anchor=anchor or self.anchor)

    def as_safe_string(self, default=_DEFAULT, anchor=None):
        """ Returns a string that might includes obfuscation where secrets are used """
        return self.as_string(anchor)

    def as_string(self, default=_DEFAULT, anchor=None):
        resolved = self.resolve()
        if isinstance(resolved, (int, float, bool)):
            resolved = str(resolved)
        if not isinstance(resolved, basestring):
            raise errors.TypeError("Expected string", anchor=anchor or self.anchor)
        return resolved


class Streamish(object):
    """
    A mixin for a class that behaves like a stream - i.e. is iterable

    This includes a default get implementation that gently unwinds
    generators and iterators
    """

    def __init__(self):
        self._buffer = []
        self._position = 0
        self._iterator = None

    def as_iterable(self, anchor=None):
        idx = 0
        while True:
            self._fill_to(idx)
            yield self._buffer[idx]
            idx += 1

    def _fill_to(self, index):
        if not self._iterator:
            self._iterator = self.get_unwinder()

        while len(self._buffer) < index+1:
            self._buffer.append(self._iterator.next())

    def get_index(self, index):
        self._fill_to(index)
        return self._buffer[index]

    def resolve_once(self):
        return [x.resolve() for x in self.as_iterable()]


class Dictish(object):

    def as_iterable(self, anchor=None):
        for key in self.keys(anchor or self.anchor):
            yield YayScalar(key)

    def as_dict(self, anchor=None):
        return self.resolve()

    def resolve_once(self):
        return dict((key, self.get_key(key).resolve()) for key in self.keys())


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
            return self.expand().as_bool(anchor or self.anchor)
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_int(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_int(anchor or self.anchor)
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_float(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_float(anchor or self.anchor)
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_number(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_number(anchor or self.anchor)
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_safe_string(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_safe_string(anchor or self.anchor)
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_string(self, default=_DEFAULT, anchor=None):
        try:
            return self.expand().as_string(anchor or self.anchor)
        except errors.NoMatching:
            if default != _DEFAULT:
                return default
            raise

    def as_dict(self, anchor=None):
        return self.expand().as_dict(anchor or self.anchor)

    def keys(self, anchor=None):
        return self.expand().keys(anchor or self.anchor)

    def as_iterable(self, anchor=None):
        return self.expand().as_iterable(anchor or self.anchor)

    def get_key(self, key):
        return self.expand().get_key(key)

    def expand_once(self):
        raise NotImplementedError("%r does not implement expand or expand_once - but proxy types must" % type(self))

    def resolve_once(self):
        return self.expand().resolve()


class Tripwire(Proxy, AST):

    def __init__(self):
        self.node = None
        self.expressions = []
        self.expanding = False

    def add_tripwire(self, expression, expected):
        self.expressions.append((expression, expected))

    def get_callable(self, key):
        p = self.node
        while p:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def expand(self):
        if not self.expanding:
            self.expanding = True
            for expr, expected in self.expressions:
                current = expr()
                if current != expected:
                    raise errors.ParadoxError("Inconsistent configuration detected - changed from %r to %r" % (expected, current), anchor=self.anchor)
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
        return self.keys()

    def __getattr__(self, key):
        return PythonicWrapper(AttributeRef(self, key))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return PythonicWrapper(SliceyThing(self, key))
        return PythonicWrapper(Subscription(self, YayScalar(key)))

    def __iter__(self):
        for val in self.as_iterable():
            yield PythonicWrapper(val)


class PythonicWrapper(Pythonic, Proxy, AST):
    def __init__(self, inner):
        self.inner = inner

    def expand_once(self):
        return self.inner.expand()

class Root(Pythonic, Proxy, AST):
    """ The root of the document
    FIXME: This needs thinking about some more
    """
    def __init__(self, node=None):
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

    def get_callable(self, key):
        p = self.node
        while p:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get_context(self, key):
        return self.node.get_key(key)

    def expand(self):
        return self.node.expand()

    def parse(self, path):
        stream = self.openers.open(path)
        from yay import parser
        return parser.parse(stream.read())

class Identifier(Proxy, AST):
    def __init__(self, identifier):
        self.identifier = identifier

    def expand_once(self):
        __context__ = "Looking up '%s' in current scope" % self.identifier
        node = self.head
        root = self.root
        while node != root:
            try:
                return node.get_context(self.identifier).expand()
            except errors.NoMatching:
                pass
            node = node.parent

        assert node == root
        return node.get_context(self.identifier).expand()

class Literal(Scalarish, AST):
    def __init__(self, literal):
        self.literal = literal
    def resolve_once(self):
        return self.literal

class ParentForm(Scalarish, AST):
    # FIXME: Understand this better...
    def __init__(self, expression_list=None):
        self.expression_list = expression_list
        if expression_list:
            expression_list.parent = self
    def resolve_once(self):
        if not self.expression_list:
            return []
        return self.expression_list.resolve()

class ExpressionList(AST):
    def __init__(self, *expressions):
        self.expression_list = list(expressions)
        for expr in self.expression_list:
            expr.parent = self

    def append(self, expression):
        self.expression_list.append(expression)

    def resolve_once(self):
        return [expr.resolve() for expr in self.expression_list]


class UnaryExpr(Scalarish, AST):

    def __init__(self, inner):
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
            return True, self.__class__(self.lhs.simplify(), self.rhs.simplify())

    def resolve_once(self):
        return self.op(self.lhs.as_number(), self.rhs.as_number())

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

class Subtract(Expr):
    op = operator.sub

class Multiply(Expr):
    op = operator.mul

class Divide(Expr):
    op = operator.truediv

class FloorDivide(Expr):
    op = operator.floordiv

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
    def resolve_once(self):
        try:
            res = self.lhs.resolve()
            if res:
                return res
        except errors.NoMatching:
            pass
        return self.rhs.resolve()

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
        try:
            return self._dict[key]
        except KeyError:
            raise errors.NoMatching("No such key '%s" % key, anchor=self.anchor)

    def keys(self):
        if not self._dict:
            self._refresh_self()
        return self._ordered_keys


class KeyDatumList(AST):

    def __init__(self, *key_data):
        self.key_data = list(key_data)

    def append(self, key_datum):
        self.key_data.append(key_datum)

class KeyDatum(AST):

    def __init__(self, key, value):
        self.key = key
        self.value = value

class AttributeRef(Proxy, AST):
    def __init__(self, primary, identifier):
        self.primary = primary
        primary.parent = self
        self.identifier = identifier

    def expand_once(self):
        __context__ = " -> Looking up subkey '%s'" % self.identifier
        return self.primary.expand().get_key(self.identifier).expand()

class LazyPredecessor(Proxy, AST):
    def __init__(self, node, identifier):
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
            raise errors.NoMatching("No such key '%s'" % key)
        return predecessor.get_key(key)

    def expand_once(self):
        if self.node.predecessor:
            parent_pred = self.node.predecessor.expand()
            try:
                pred = parent_pred.get_key(self.identifier)
            except errors.NoMatching:
                raise errors.NoPredecessor
            return pred.expand()
        raise errors.NoPredecessor

class UseMyPredecessorStandin(Proxy, AST):
    def __init__(self, node):
        # This is a sideways reference! No parenting...
        self.node = node

    @property
    def predecessor(self):
        return self.node.predecessor

    def get_key(self, key):
        try:
            return self.expand().get_key(key)
        except NoPredecessor:
            raise errors.NoMatching("No such key '%s'" % key)

    def expand_once(self):
        return self.node.predecessor.expand()


class NoPredecessorStandin(Proxy, AST):

    predecessor = None

    def expand(self):
        raise errors.NoPredecessor("Node has no predecessor")


class Subscription(Proxy, AST):
    def __init__(self, primary, *expression_list):
        self.primary = primary
        primary.parent = self
        self.expression_list = list(expression_list)
        if len(self.expression_list) > 1:
            raise errors.SyntaxError("Keys must be scalars, not tuples", anchor=self.anchor)
        for e in self.expression_list:
            e.parent = self

    def expand_once(self):
        return self.primary.expand().get_key(self.expression_list[0].resolve()).expand()

class SimpleSlicing(Streamish, AST):

    """
    Implements simple slices of any ``AST`` type that implements the
    ``Streamish`` interface.

    Because of the default methods provided by the ``Streamish`` mixin this
    class only needs to implement ``get_unwinder``. This yields objects that
    match the specified stride.
    """

    def __init__(self, primary, short_slice):
        super(SimpleSlicing, self).__init__()
        self.primary = primary
        primary.parent = self
        self.short_slice = short_slice
        short_slice.parent = self

    def get_unwinder(self, anchor=None):
        lower_bound = self.short_slice.lower_bound.resolve()
        upper_bound = self.short_slice.upper_bound.resolve()
        stride = self.short_slice.stride.resolve()

        for i in range(lower_bound, upper_bound, stride):
            yield self.primary.expand().get_index(i)

class ExtendedSlicing(Streamish, AST):

    """
    Implements extended slices of any ``AST`` type that implements the
    ``Streamish`` interface.

    Because of the default methods provided by the ``Streamish`` mixin this
    class only needs to implement ``get_unwinder``. This yields objects that
    match the specified strides.
    """

    def __init__(self, primary, slice_list):
        super(ExtendedSlicing, self).__init__()
        self.primary = primary
        primary.parent = self
        self.slice_list = slice_list
        slice_list.parent = self

        if len (self.slice_list.slice_list) > 1:
            raise errors.SyntaxError("Only a single slice at a time is supported", anchor=self.anchor)

    def get_unwinder(self, anchor=None):
        short_slice = self.slice_list.slice_list[0]

        lower_bound = short_slice.lower_bound.resolve()
        upper_bound = short_slice.upper_bound.resolve()
        stride = short_slice.stride.resolve()

        for i in range(lower_bound, upper_bound, stride):
            yield self.primary.expand().get_index(i)

class SliceList(AST):
    def __init__(self, slice_item):
        self.slice_list = [slice_item]

    def append(self, slice_item):
        self.slice_list.append(slice_item)

class Slice(AST):
    def __init__(self, lower_bound=None, upper_bound=None, stride=None):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.stride = stride or YayScalar(1)


import re

class Call(Proxy, AST):

    def __init__(self, primary, args=None, kwargs=None):
        self.primary = primary
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
                k = kwargs[kwarg.identifier.identifier] = kwarg.expression.clone()

        try:
            macro = self.root.get_callable(self.primary.identifier)
            call = CallDirective(self.primary, None)
            node = Context(call, kwargs)
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
        self.primary = primary
        if not self.primary.identifier in self.allowed:
            raise errors.NoMatching("Could not find '%s'" % self.primary.identifier)

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
        return bind(result)


class ArgumentList(AST):
    def __init__(self, args, kwargs=None):
        self.args = args
        self.kwargs = kwargs

class PositionalArguments(AST):
    def __init__(self, *expressions):
        self.args = list(expressions)

    def append(self, expression):
        self.args.append(expression)

class KeywordArguments(AST):
    def __init__(self, *keyword_items):
        self.kwargs = list(keyword_items)

    def append(self, keyword_item):
        self.kwargs.append(keyword_item)

class Kwarg(AST):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression

class TargetList(AST):
    def __init__(self, *targets):
        self.v = list(targets)

    def append(self, target):
        self.v.append(target)

class ParameterList(AST):
    def __init__(self, defparameter):
        self.parameter_list = [defparameter]

    def append(self, defparameter):
        self.parameter_list.append(defparameter)

class DefParameter(AST):
    def __init__(self, parameter, expression=None):
        self.parameter = parameter
        self.expression = expression

class Sublist(AST):
    def __init__(self, parameter):
        self.sublist = [parameter]

    def append(self, parameter):
        self.sublist.append(parameter)

class YayList(Streamish, AST):
    def __init__(self, *items):
        self.value = list(items)
        for x in self.value:
            x.parent = self

    def append(self, item):
        self.value.append(item)
        item.parent = self

    def get_key(self, idx):
        return self.get_index(idx)

    def get_index(self, idx):
        try:
            idx = int(idx)
        except ValueError:
            raise errors.TypeError("Expected integer", anchor=self.anchor)

        if idx < 0:
            raise errors.TypeError("Index must be greater than 0", anchor=self.anchor)
        elif idx >= len(self.value):
            raise errors.TypeError("Index out of range", anchor=self.anchor)

        return self.value[idx]

    def as_iterable(self, anchor=None):
        return iter(self.value)

class YayDict(Dictish, AST):

    """ A dictionary in yay may redefine items, so update merely appends. The
    value is a list of 2-tuples """

    def __init__(self, value=None):
        self.values = {}
        if value:
            for (k, v) in value:
                self.update(k, v)

    def update(self, k, v):
        try:
            predecessor = self.get_key(k)
        except errors.NoMatching:
            predecessor = LazyPredecessor(self, k)

        v.parent = self
        self.values[k] = v

        # Respect any existing predecessors rather than blindly settings v.predecessor
        while v.predecessor and not isinstance(v.predecessor, (NoPredecessorStandin, LazyPredecessor)):
            v = v.predecessor
            v.parent = self
        v.predecessor = predecessor

    def merge(self, other_dict):
        # This function should ONLY be called by parser and ONLY to merge 2 YayDict nodes...
        assert isinstance(other_dict, YayDict)
        for k, v in other_dict.values.items():
            self.update(k, v)

    def keys(self, anchor=None):
        keys = set(self.values.keys())
        try:
            keys.update(self.predecessor.keys(anchor=self.anchor))
        except errors.NoPredecessor:
            pass
        return sorted(list(keys))

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
        raise errors.NoMatching("Key '%s' not found" % key)


class YayExtend(Streamish, AST):
    def __init__(self, value):
        super(YayExtend, self).__init__()
        self.value = value
        value.parent = self

    def get_unwinder(self, anchor=None):
        try:
            for node in self.predecessor.as_iterable(anchor or self.anchor):
                yield node
        except errors.NoPredecessor:
            pass

        for node in self.value.as_iterable(anchor or self.anchor):
            yield node


class YayScalar(Scalarish, AST):
    def __init__(self, value):
        try:
            self.value = int(value)
        except ValueError:
            try:
                self.value = float(value)
            except ValueError:
                self.value = value

    def resolve_once(self):
        return self.value

class YayMultilineScalar(Scalarish, AST):

    chompers = {
        '>': "chomp_fold",
        '|': "chomp_literal",
        '|+': "chomp_keep",
        '|-': "chomp_strip",
    }

    def __init__(self, value, mtype):
        self.__value = value
        self.mtype = mtype
        self.chomper = getattr(self, self.chompers[self.mtype])

    @property
    def value(self):
        return self.chomper(self.__value)

    @staticmethod
    def chomp_fold(value):
        """
        For multiline strings introduced with only '>'.

        Folding allows long lines to be broken anywhere a single space
        character separates two non-space characters.
        """
        # This is what pyYAML does
        #
        # Unfortunately, folding rules are ambiguous.
        #
        # This is the folding according to the specification:
        #
        #if folded and line_break == u'\n'   \
        #        and leading_non_space and self.peek() not in u' \t':
        #    if not breaks:
        #        chunks.append(u' ')
        #else:
        #    chunks.append(line_break)

        v = []
        lines = value.split('\n')
        for i, l in enumerate(lines):
            if l:
                v.append(l)
                try:
                    peek = not lines[i+1] or lines[i+1][0] in ' \t'
                except IndexError:
                    peek = False
                if not re.match('^\s', l)  and not peek:
                    v.append(' ')
                else:
                    v.append('\n')
        rv = "".join(v)
        return rv

    @staticmethod
    def chomp_literal(value):
        """
        For multiline strings introduced with only '|'.

        In this case, the final line break character is preserved in the
        scalar's content. However, any trailing empty lines are excluded
        from the scalar's content.
        """
        return re.sub("[\n]+", "\n", value)

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

        return value.rstrip()

    def append(self, value):
        self.__value = self.__value + value

class YayMerged(Scalarish, AST):
    """ Combined scalars and templates """

    def __init__(self, *v):
        self.value = list(v)
        for v in self.value:
            v.parent = self

    def append(self, v):
        self.value.append(v)
        v.parent = self

    def prepend(self, value):
        self.value.insert(0, value)
        value.parent = self

    def resolve_once(self):
        return "".join(str(v.resolve()) for v in self.value)

class Stanzas(Proxy, AST):
    def __init__(self, *stanzas):
        self.value = UseMyPredecessorStandin(self)
        for s in stanzas:
            self.append(s)

    def append(self, stanza):
        stanza.predecessor = self.value or NoPredecessorStandin()
        stanza.parent = self
        self.value = stanza

    def get_callable(self, key):
        p = self.value
        while p and p != self.predecessor:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get_context(self, key):
        p = self.value
        while p and p != self.predecessor:
            try:
                return p.get_context(key)
            except errors.NoMatching:
                pass
            p = p.predecessor
        raise errors.NoMatching("Could not find '%s'" % key)

    def expand(self):
        return self.value.expand()

class Directives(Proxy, AST):
    def __init__(self, *directives):
        self.value = UseMyPredecessorStandin(self)
        for d in directives:
            self.append(d)

    def append(self, directive):
        directive.parent = self
        directive.predecessor = self.value or NoPredecessorStandin()
        self.value = directive

    def get_callable(self, key):
        p = self.value
        while p and p != self.predecessor:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get_context(self, key):
        p = self.value
        while p and p != self.predecessor:
            try:
                return p.get_context(key)
            except errors.NoMatching:
                pass
            p = p.predecessor
        raise errors.NoMatching("Could not find '%s'" % key)

    def expand(self):
        return self.value.expand()

class Include(Proxy, AST):

    def __init__(self, expr):
        self.expr = expr
        expr.parent = self
        self.detector = []
        self.expanding = False

    def get_callable(self, key):
        try:
            expanded = self.expand()
        except errors.NoPredecessor:
            raise errors.NoMatching("Could not find a macro called '%s'" % key)

        p = expanded
        while p:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor

        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get_key(self, key):
        if self.expanding:
            try:
                return self.predecessor.get_key(key)
            except errors.NoPredecessor:
                raise errors.NoMatching("No such key '%s'" % key)

        if key in self.detector:
            raise errors.NoMatching("'%s' not found" % key)
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
        expr = self.expr.resolve()
        self.expanding = False

        expanded = self.root.parse(expr)
        expanded.predecessor = self.predecessor
        expanded.parent = self.parent

        t = Tripwire()
        t.anchor = self.anchor
        t.add_tripwire(self.expr.resolve, expr)
        t.node = expanded

        return True, t


class Search(AST):

    def __init__(self, expr):
        self.expr = expr

class Configure(AST):

    def __init__(self, key, node):
        self.key = key
        self.node = node

class Set(Proxy, AST):

    def __init__(self, var, expr):
        self.var = var
        var.parent = self

        self.expr = expr
        expr.parent = self

    def get_context(self, key):
        if key == self.var.identifier:
            return self.expr
        return super(Set, self).get_context(key)

    def expand_once(self):
        return self.predecessor


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

        t = Tripwire()
        t.anchor = self.anchor

        self.passthrough_mode = True
        try:
            cond = self.condition.as_bool()
        finally:
            self.passthrough_mode = False

        t.add_tripwire(self.condition.as_bool, cond)

        if cond:
            t.node = self.on_true.expand()
        elif self.on_false:
            t.node = self.on_false.expand()
        else:
            t.node = self.predecessor.expand()
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
        value = self.expr.resolve()
        self.expanding = False

        t = Tripwire()
        t.add_tripwire(self.expr.resolve, value)
        t.anchor = self.anchor

        for case in self.cases.cases:
            if case.key == value:
                t.node = case.node.expand()
                return True, t

        raise NoMatching("Select does not have key '%s'" % value, anchor=self.anchor)


class CaseList(AST):
    def __init__(self, *cases):
        self.cases = []
        [self.append(c) for c in cases]

    def append(self, case):
        case.parent = self
        self.cases.append(case)

class Case(AST):
    def __init__(self, key, node):
        self.key = key
        self.node = node
        node.parent = self

class Create(Proxy, AST):
    def __init__(self, target, node):
        self.target = target
        self.node = node

    @cached
    def expand(self):
        modname, classname = self.target.as_string().split(":", 1)
        try:
            mod = __import__(modname, globals(), locals(), ['tofu'])
        except ImportError:
            raise errors.NoMatching("Could not import '%s'" % modname)

        if not hasattr(mod, classname):
            raise errors.NoMatching("Module '%s' has no class '%s'" % (modname, classname))

        klass = getattr(mod, classname)

        if not issubclass(klass, PythonClass):
            raise errors.TypeError("'%s' is not usable from Yay" % classname)

        node = klass(self.node.clone())
        node.parent = self
        node.anchor = self.anchor
        node.predecessor = self.predecessor

        return True, node


class Macro(Proxy, AST):
    def __init__(self, target, node):
        self.target = target
        self.node = node

    def get_callable(self, key):
        if key == self.target.identifier:
            return self
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def expand_once(self):
        return self.predecessor.expand()

class YayClass(Proxy, AST):
    def __init__(self, target, node):
        self.target = target
        self.node = node

    def get_callable(self, key):
        if key == self.target.identifier:
            return self
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def construct(self, params):
        base = self.node.clone()
        # context = Context(base, {"self": base})

        params = params.clone()
        params.predecessor = base

        context = Context(params, {"self": params})
        base.parent = context

        return context

    def expand_once(self):
        return self.predecessor.expand()

class CallDirective(Proxy, AST):
    def __init__(self, target, node):
        self.target = target
        self.node = node

    def expand_once(self):
        macro = self.root.get_callable(self.target.identifier)
        clone = macro.node.clone()
        if not self.node:
            clone.parent = self
            return clone.expand()
        context = Context(clone, self.node.expand().values)
        context.parent = self
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

    def get_unwinder(self, anchor=None):
        for item in self.in_clause.as_iterable(anchor or self.anchor):
            # self.target.identifier: This probably shouldn't be an identifier
            c = Context(self.node.clone(), {self.target.identifier: item})
            c.parent = self.parent

            if self.if_clause:
                f = self.if_clause.clone()
                f.parent = c
                if not f.resolve():
                    continue

            for node in c.as_iterable(anchor or self.anchor):
                yield node


class Template(Proxy, AST):

    def __init__(self, value):
        self.value = value
        value.parent = self

    def expand_once(self):
        return self.value.expand()


class Context(Proxy, AST):

    def __init__(self, value, context):
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

    def get_unwinder(self, anchor=None):
        for node in self.list_for.expressions.as_iterable(anchor or self.anchor):
            ctx = Context(self.expression.clone(), {self.list_for.targets.identifier: node})
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
        self.expression = expression
        self.iterator = iterator

class Comprehension(AST):
    def __init__(self, expression, comp_for):
        self.expression = expression
        self.comp_for = comp_for

class CompFor(AST):
    def __init__(self, targets, test, iterator=None):
        self.targets = targets
        self.test = test
        self.iterator = iterator

class CompIf(AST):
    def __init__(self, expression, iterator=None):
        self.expression = expression
        self.iterator = iterator

class GeneratorExpression(AST):
    def __init__(self, expression, comp_for):
        self.expression = expression
        self.comp_for = comp_for

class DictComprehension(AST):
    def __init__(self, key, value, comp_for):
        self.key = key
        self.value = value
        self.comp_for = comp_for

class SetDisplay(AST):
    def __init__(self, v):
        self.v = v

class StringConversion(AST):
    def __init__(self, v):
        self.v = v

class LambdaForm(AST):
    def __init__(self, expression, params=None):
        self.expression = expression
        self.params = params

class Comment(AST):
    def __init__(self, v):
        self.v = v


class PythonClass(Proxy, AST):

    """
    This is a Mixin for writing nodes that can be created with the ``create`` syntax
    """

    def __init__(self, params):
        # Dictionary to hold data created/fetched by this class
        self.metadata = {}

        # Object to exposed metadata exported by this class to yay
        self.class_provided = PythonDict(self.metadata)
        self.class_provided.parent = self
        self.class_provided.predecessor = params

        # Node containing metadata provided by the user
        params.parent = self
        self.params = PythonicWrapper(params)
        self.params.parent = self

        self.stale = True

    def apply(self):
        raise NotImplementedError(self.apply)

    def expand_once(self):
        if self.stale:
            self.apply()
            self.stale = False

        return self.class_provided.expand()


class PythonIterable(Streamish, AST):

    def __init__(self, iterable):
        super(PythonIterable, self).__init__()
        self.iterable = iterable

    def get_unwinder(self, anchor=None):
        for node in self.iterable:
            obj = bind(node)
            obj.parent = self
            yield obj


class PythonDict(Dictish, AST):

    def __init__(self, dict):
        self.dict = dict
        #FIXME: We should either have a fake anchor or generate one by inspecting the frame
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

        raise errors.NoMatching("No key '%s'" % key)

    def keys(self, anchor=None):
        seen = set()
        try:
            for key in self.predecessor.keys(anchor or self.anchor):
                seen.add(key)
                yield key
        except errors.NoPredecessor:
            pass

        for key in sorted(self.dict.keys()):
            if key in seen:
                continue
            yield key


bindings = [
    (inspect.isgenerator,                                        PythonIterable),
    (lambda v: isinstance(v, list),                              PythonIterable),
    (lambda v: isinstance(v, dict),                              PythonDict),
    (lambda v: isinstance(v, (int, float, basestring, bool)),    YayScalar),
]

def bind(v):
    for detector, wrapper in bindings:
        if detector(v):
            return wrapper(v)
    raise error.TypeError("Encountered unbindable object")


AST._predecessor = NoPredecessorStandin()
