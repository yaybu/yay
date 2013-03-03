import operator


class AST(object):

    lineno = 0
    predecessor = None

    def resolve(self):
        """
        Resolve an object into a simple type, like a string or a dictionary.

        Node does not provide an implementation of this, all subclasses should
        implemented it.
        """
        raise NotImplementedError(self.resolve)

    def expand(self):
        """
        Generate a simplification of this object that can replace it in the graph
        """
        return self

    def get_context(self, key):
        """
        Look up value of ``key`` and return it.

        This doesn't do any resolving, the return value will be a subclass of Node.
        """
        return self.parent.get_context(key)

    def get_root(self):
        """
        Find and return the root of this document.
        """
        return self.parent.get_root()

    def error(self, exc):
        raise ValueError("Runtime errors deliberately nerfed for PoC")

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
        for k, v in self.__vars().items():
            instance.__dict__[k] = _clone(v)

        return instance

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__vars())

    def __vars(self):
        """ Return the members without the lineno """
        d = self.__dict__.copy()
        for var in ('lineno', 'parent'):
            if var in d:
                del d[var]
        return d

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__vars() == other.__vars()

class Root(AST):
    """ The root of the document 
    FIXME: This needs thinking about some more
    """
    def __init__(self, node):
        self.node = node
        node.parent = self

    def get_root(self):
        return self

    def get_context(self, key):
        return self.node.get(key)

    def resolve(self):
        return self.node.resolve()

class Identifier(AST):
    def __init__(self, identifier):
        self.identifier = identifier

    def expand(self):
        return self.get_context(self.identifier)

    def resolve(self):
        return self.expand().resolve()

class Literal(AST):
    def __init__(self, literal):
        self.literal = literal
    def resolve(self):
        return self.literal

class ParentForm(AST):
    def __init__(self, expression_list=None):
        self.expression_list = expression_list
        if expression_list:
            expression_list.parent = self

class ExpressionList(AST):
    def __init__(self, *expressions):
        self.expression_list = list(expressions)
        for expr in self.expression_list:
            expr.parent = self

    def append(self, expression):
        self.expression_list.append(expression)

class Power(AST):
    def __init__(self, primary, power=None):
        self.primary = primary
        primary.parent = self
        self.power = power
        power.parent = self

class UnaryMinus(AST):
    """ The unary - (minus) operator yields the negation of its numeric
    argument. """

    def __init__(self, u_expr):
        self.u_expr = u_expr
        u_expr.parent = self

    def resolve(self):
        return -self.u_expr.resolve()

class Invert(AST):
    """ The unary ~ (invert) operator yields the bitwise inversion of its
    plain or long integer argument. The bitwise inversion of x is defined as
    -(x+1). It only applies to integral numbers. """
    def __init__(self, u_expr):
        self.u_expr = u_expr
        u_expr.parent = self

    def resolve(self):
        return ~self.u_expr.resolve()

class Expr(AST):
    operators = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        ">": operator.gt,
        "<=": operator.le,
        ">=": operator.ge,
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.div,
        "or": operator.or_,
        "and": operator.and_,
        "not in": lambda x, y: not x in y,
    }

    def __init__(self, lhs, rhs, operator):
        self.lhs = lhs
        lhs.parent = self
        self.rhs = rhs
        rhs.parent = self
        self.operator = operator
        self.op = self.operators[operator]

    def resolve(self):
        l = self.lhs.resolve()
        r = self.rhs.resolve()
        return self.op(l, r)

class Not(AST):
    def __init__(self, value):
        self.value = value 
        value.parent = self

    def resolve(self):
        return not self.value.resolve()

class ConditionalExpression(AST):
    def __init__(self, or_test, if_clause, else_clause):
        self.or_test = or_test
        self.if_clause = if_clause
        self.else_clause = else_clause

class ListDisplay(AST):
    def __init__(self, expression_list=None):
        self.expression_list = expression_list

class DictDisplay(AST):

    def __init__(self, key_datum_list=None):
        self.key_datum_list = key_datum_list

class KeyDatumList(AST):

    def __init__(self, *key_data):
        self.key_data = list(key_data)

    def append(self, key_datum):
        self.key_data.append(key_datum)

class KeyDatum(AST):

    def __init__(self, key, value):
        self.key = key
        self.value = value

class AttributeRef(AST):
    def __init__(self, primary, identifier):
        self.primary = primary
        primary.parent = self
        self.identifier = identifier

class Subscription(AST):
    def __init__(self, primary, expression_list):
        self.primary = primary
        self.expression_list = expression_list

class SimpleSlicing(AST):
    def __init__(self, primary, short_slice):
        self.primary = primary
        self.short_slice = short_slice

class ExtendedSlicing(AST):
    def __init__(self, primary, slice_list):
        self.primary = primary
        self.slice_list = slice_list

class SliceList(AST):
    def __init__(self, slice_item):
        self.slice_list = [slice_item]

    def append(self, slice_item):
        self.slice_list.append(slice_item)

class Slice(AST):
    def __init__(self, lower_bound=None, upper_bound=None, stride=1):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.stride = stride

class Call(AST):
    def __init__(self, primary, args=None, kwargs=None):
        self.primary = primary
        self.args = args
        self.kwargs = kwargs

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

class YayList(AST):
    def __init__(self, *items):
        self.value = list(items)
        for x in self.value:
            x.parent = self

    def append(self, item):
        self.value.append(item)
        item.parent = self

    def get_context(self, key):
        return super(YayList, self).get_context(key)

    def resolve(self):
        l = []
        for i in self.value:
            l.append(i.resolve())
        return l

    def __iter__(self):
        return iter(self.value)

class YayDict(AST):

    """ A dictionary in yay may redefine items, so update merely appends. The
    value is a list of 2-tuples """

    def __init__(self, value=None):
        self.values = {}

        if value:
            for k, v in value:
                v.predecessor = self.values.get(k, None)
                v.parent = self
                self.values[k] = v

        #if value is None:
        #    self.value = []
        #else:
        #    self.value = value
        #    for k, v in self.value:
        #        v.parent = self

    def update(self, value):
        for k, v in value:
            v.predecessor = self.values.get(k, None)
            v.parent = self
            self.values[k] = v

        #self.value.extend(l)
        #for k, v in l:
        #    v.parent = self

    def get(self, key):
        if key in self.values:
            return self.values[key]
        if self.predecessor:
            return self.predecessor.expand().get(key)
        raise KeyError("Key '%s' not found" % key)

    def __iter__(self):
        return iter(self.values.items())

    def resolve(self):
        d = {}
        if self.predecessor:
            d = self.predecessor.resolve()
        for k, v in self.values.items():
            d[k] = v.resolve()

        #d = {}
        #for a, b in self.value:
        #    d[a] = b
        #e = {}
        #for k, v in d.items():
        #    e[k] = v.resolve()

        return d

class YayExtend(AST):
    def __init__(self, key, value):
        self.value = {key: value}

    def get(self, idx, default=None):
        return BoxingFactory.box(self.resolve()[int(idx)])

    def expand(self):
        if not self.chain:
            return self.value.expand()

        chain = self.chain.expand()
        if not hasattr(chain, "__iter__"):
            self.error("You can only append to list types")

        value = self.value.expand()
        if not hasattr(value, "__iter__"):
            self.error("You must append a list to this field")

        # we initialize this sequence weirdly as we dont want to reparent the nodes we are appending
        s = YayList([])
        s.value = list(iter(chain)) + list(iter(value))
        s.parent = self.parent
        return s

    def resolve(self):
        return self.expand().resolve()

class YayScalar(AST):
    def __init__(self, value):
        self.value = value

    def resolve(self):
        return self.value

class YayMerged(AST):
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

    def resolve(self):
        return "".join(str(v.resolve()) for v in self.value)

class Stanzas(AST):
    def __init__(self, *stanzas):
        self.value = list(stanzas)

    def append(self, stanza):
        self.value.append(stanza)

    def resolve(self):
        l = []
        for i in self.value:
            l.append(i.resolve())
        return l

class Directives(AST):
    def __init__(self, *directives):
        self.value = list(directives)
        for d in self.value:
            d.parent = self

    def append(self, directive):
        self.value.append(directive)

    def resolve(self):
        # FIXME: This needs careful planning
        return self.value[-1].resolve()

class Include(AST):

    def __init__(self, expr):
        self.expr = expr

class Search(AST):

    def __init__(self, expr):
        self.expr = expr

class Configure(AST):

    def __init__(self, key, node):
        self.key = key
        self.node = node

class Set(AST):

    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

    def __repr__(self):
        return "<Set %r = %r>" % (self.var, self.expr)


class If(AST):

    def __init__(self, condition, result, elifs=None, else_=None):
        self.condition = condition
        self.result = result
        self.elifs = elifs
        self.else_ = else_

class ElifList(object):
    def __init__(self, *elifs):
        self.elifs = list(elifs)

    def append(self, elif_):
        self.elifs.append(elif_)

class Elif(object):
    def __init__(self, condition, node):
        self.condition = condition
        self.node = node

class Select(AST):

    def __init__(self, expr, cases):
        self.expr = expr
        self.cases = cases

class CaseList(object):
    def __init__(self, *cases):
        self.cases = list(cases)

    def append(self, case):
        self.cases.append(case)

class Case(object):
    def __init__(self, key, node):
        self.key = key
        self.node = node


def flatten(lst):
    for itm in lst:
        if isinstance(itm, list):
            for x in flatten(itm):
               yield x
        else:
            yield itm

class For(AST):

    def __init__(self, target, in_clause, node, if_clause=None):
        self.target = target
        target.parent = self
        self.if_clause = if_clause
        if if_clause:
            if_clause.parent = self
        self.in_clause = in_clause
        in_clause.parent = self
        self.node = node
        node.parent = self

    def iterate_expanded(self):
        lst = []

        for item in self.in_clause.expand():
            # self.target.identifier: This probably shouldn't be an identifier
            c = Context(self.node.clone(), {self.target.identifier: item.clone()})
            c.parent = self.parent

            if self.if_clause:
                f = self.if_clause.clone()
                f.parent = c
                if not f.resolve():
                    continue

            lst.append(c)

        sq = YayList(*lst)
        sq.parent = self.parent
        return sq

    def resolve(self):
        return list(flatten([x.resolve() for x in self.iterate_expanded()]))

class Template(AST):
    def __init__(self, *value):
        self.value = list(value)
        for v in self.value:
            v.parent = self

    def resolve(self):
        return ''.join(str(v.resolve()) for v in self.value)

class Context(AST):

    def __init__(self, value, context):
        self.value = value
        self.value.parent = self
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

    def expand(self):
        return self.value.expand()

    def resolve(self):
        return self.value.resolve()
