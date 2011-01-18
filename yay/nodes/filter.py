
from yay.nodes import Node

class Filter(Node):

    def __init__(self, container, filter_expression):
        self.container = container
        self.filter_expression = filter_expression

    def resolve(self, context):
        resolved = self.container.resolve(context)
        if not isinstance(resolved, list):
            raise ValueError("Expected sequence, got '%s'" % resolved)

        filtered = []
        for r in resolved:
            #FIXME: Do some filtering here!
            filtered.append(r)

        return filtered

    def __repr__(self):
        return "Filter(%s, %s)" % (self.container, self.filter_expression)
