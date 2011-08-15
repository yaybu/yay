
from yay.nodes import Node, Sequence, Context

class Filter(Node):

    def __init__(self, container, filter_expression):
        self.container = container
        if container:
            container.set_parent(self)
        self.filter_expression = filter_expression
        filter_expression.set_parent(self)

    def semi_resolve(self):
        resolved = self.container.semi_resolve()

        filtered = []
        for r in resolved:
            ctx = Context(self.filter_expression.clone(), {"@": r})
            r.set_parent(ctx)
            ctx.set_parent(self.parent)
            if ctx.resolve():
                filtered.append(r)

        return Sequence(filtered)

    def get(self, idx):
        return self.semi_resolve().get(idx)

    def resolve(self):
        return self.semi_resolve().resolve()

    def __repr__(self):
        return "Filter(%s, %s)" % (self.container, self.filter_expression)

    def walk(self):
        yield self.container
        yield self.filter_expression

    def clone(self):
        return Filter(self.container.clone(), self.filter_expression.clone())

