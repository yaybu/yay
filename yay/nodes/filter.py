
from yay.nodes import Node, Sequence, Context

class Filter(Node):

    def __init__(self, container, filter_expression):
        self.container = container
        if container:
            container.set_parent(self)
        self.filter_expression = filter_expression
        filter_expression.set_parent(self)

    def semi_resolve(self, context):
        resolved = self.container.semi_resolve(context)

        filtered = []
        for r in resolved:
            ctx = Context(self.filter_expression.clone(), {"@": r})
            r.set_parent(ctx)
            ctx.set_parent(self.parent)
            if ctx.resolve(context):
                filtered.append(r)

        return Sequence(filtered)

    def get(self, context, idx):
        return self.semi_resolve(context).get(context, idx)

    def resolve(self, context):
        return self.semi_resolve(context).resolve(context)

    def __repr__(self):
        return "Filter(%s, %s)" % (self.container, self.filter_expression)

    def walk(self, context):
        yield self.container
        yield self.filter_expression

    def clone(self):
        return Filter(self.container.clone(), self.filter_expression.clone())

