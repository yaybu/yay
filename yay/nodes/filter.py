
from yay.nodes import Node, Sequence, Context

class Filter(Node):

    """
    Filter an iterable according to an XPath style selector

    It will be created when the parser encounters something like::

        example: ${foo[@.baz < 5]}

    This will check every object in the sequence ``foo`` for a property
    called ``baz`` with a value less than 5. The output is a sequence.
    """

    def __init__(self, container, filter_expression):
        self.container = container
        if container:
            container.set_parent(self)
        self.filter_expression = filter_expression
        filter_expression.set_parent(self)

    def expand(self):
        resolved = self.container.expand()

        filtered = []
        for r in resolved:
            ctx = Context(self.filter_expression.clone(), {"@": r})
            r.set_parent(ctx)
            ctx.set_parent(self.parent)
            if ctx.resolve():
                filtered.append(r)

        return Sequence(filtered)

    def get(self, idx):
        return self.expand().get(idx)

    def resolve(self):
        return self.expand().resolve()

    def __repr__(self):
        return "Filter(%s, %s)" % (self.container, self.filter_expression)

    def walk(self):
        yield self.container
        yield self.filter_expression

    def clone(self):
        return Filter(self.container.clone(), self.filter_expression.clone())

