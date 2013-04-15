
# See https://github.com/tinkerpop/gremlin/wiki/Gremlin-Steps

class PipeType(type):

    registry = {}

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if hasattr(cls, "name"):
            if cls.name in meta.registry:
                raise KeyError("Redefinition of pipe '%s'" % cls.name)
            meta.registry[cls.name] = cls
        return cls


class Pipe(object):

    __metaclass__ = PipeType

    def __init__(self, source):
        self.source = source

    def __call__(self, *args, **kwargs):
        return self.__class__(self.source, *args, **kwargs)

    def __getattr__(self, key):
        if key in PipeType.registry:
            return PipeType.registry[key](self)
        raise AttributeError

    def __dir__(self):
        return list(super(Pipe, self).__dir__() + PipeType.registry.keys())

    def apply(self, stack):
        raise NotImplementedError(self.apply)

    def iter_with_stack(self):
        for stack in self.source.iter_with_stack():
            for child in self.apply(stack):
                newstack = list(stack)
                newstack.append(child)
                yield newstack

    def __iter__(self):
        for stack in self.iter_with_stack():
            yield stack[-1]


class Start(Pipe):

    def __init__(self, start):
        self.start = start

    def iter_with_stack(self):
        yield [self.start]


class Identity(Pipe):
    """ Emit the incoming object unchanged """
    name = "_"

    def __init__(self, source):
        self.source = source

    def apply(self, stack):
        yield stack[-1]


class Step(Pipe):
    """ A step defined by a callable or lamda """

    name = "step"

    def __init__(self, source, step):
        self.source = source
        self.step = step

    def apply(self, stack):
        yield self.step(stack[-1])


class Id(Pipe):
    """ Returns the identifier of the element """
    name = "id"

    def apply(self, stack):
        yield id(stack[-1])

class Label(Pipe):
    """ Returns the label of the edge """
    name = "label"

    def apply(self, stack):
        yield stack[-1].label

class Outgoing(Pipe):
    """ Returns the label of the edge """
    name = "out"

    def __init__(self, source, *labels):
        super(Outgoing, self).__init__(source)
        self.labels = labels

    def apply(self, stack):
        for child in stack[-1]._outgoing:
            if self.labels and child.label not in self.labels:
                continue
            yield child.to_

class OutgoingE(Pipe):
    """ Returns the label of the edge """
    name = "outE"

    def __init__(self, source, *labels):
        super(OutgoingE, self).__init__(source)
        self.labels = labels

    def apply(self, stack):
        for child in stack[-1]._outgoing:
            if self.labels and child.label not in self.labels:
                continue
            yield child

class Incoming(Pipe):
    """ Returns the label of the edge """
    name = "in_"

    def __init__(self, source, *labels):
        super(Incoming, self).__init__(source)
        self.labels = labels

    def apply(self, stack):
        for child in stack[-1]._incoming:
            if self.labels and child.label not in self.labels:
                continue
            yield child.from_

class IncomingE(Pipe):
    """ Returns the label of the edge """
    name = "inE"

    def __init__(self, source, *labels):
        super(IncomingE, self).__init__(source)
        self.labels = labels

    def apply(self, stack):
        for child in stack[-1]._incoming:
            if self.labels and child.label not in self.labels:
                continue
            yield child

class Both(Pipe):
    """ Returns the label of the edge """
    name = "both"

    def __init__(self, source, *labels):
        super(Both, self).__init__(source)
        self.labels = labels

    def apply(self, stack):
        for child in stack[-1]._incoming:
            if self.labels and child.label not in self.labels:
                continue
            yield child.from_
        for child in stack[-1]._outgoing:
            if self.labels and child.label not in self.labels:
                continue
            yield child.to_


class BothE(Pipe):
    """ Returns the label of the edge """
    name = "bothE"

    def __init__(self, source, *labels):
        super(BothE, self).__init__(source)
        self.labels = labels

    def apply(self, stack):
        for child in stack[-1]._incoming:
            if self.labels and child.label not in self.labels:
                continue
            yield child
        for child in stack[-1]._outgoing:
            if self.labels and child.label not in self.labels:
                continue
            yield child


class OutV(Pipe):
    """ Returns the label of the edge """
    name = "outV"

    def apply(self, stack):
        yield stack[-1].from_

class InV(Pipe):
    """ Returns the label of the edge """
    name = "inV"

    def apply(self, stack):
        yield stack[-1].to_

class BothV(Pipe):
    """ Returns the label of the edge """
    name = "bothV"

    def apply(self, stack):
        yield stack[-1].from_
        yield stack[-1].to_


class TransformStep(Step):
    name = "transform"


class FilterStep(Step):
    name = "filter"


class Back(Pipe):
    name = "back"

    def __init__(self, source, back):
        self.source = source
        self.back = back

    def apply(self):
        yield stack[-self.back]


class Dedup(Pipe):
    name = "dedup"

    def __init__(self, source):
        self.source = source
        self.seen = set()

    def apply(self, stack):
        id_ = id(stack[-1])
        if id_ in self.seen:
            return
        self.seen.add(id_)
        yield stack[-1]


class First(Identity):
    """ Returns the first element to pass the criteria """
    name = "first"

    def iter_with_stack(self):
        iterator = iter(super(First, self).iter_with_stack())
        yield iterator.next()


if __name__ == "__main__":
    if_ = If()
    if_.guard = Literal()
    if_.on_true = Literal()
    if_.on_false = Literal()

    print "if_.guard", if_.guard
    print "if_.guard.parent", if_.guard.parent

    print list(if_.q.out.in_.dedup)
