
from yay.nodes import Node

class Include(Node):
    
    def __init__(self, expr):
        super(Include, self).__init__()
        self.expr = expr

class Search(Node):
    
    def __init__(self, expr):
        super(Search, self).__init__()
        self.expr = expr

class Configure(Node):
    
    def __init__(self, key, node):
        super(Configure, self).__init__()
        self.key = key
        self.node = node
        
class Set(Node):
    
    def __init__(self, var, expr):
        super(Set, self).__init__()
        self.var = var
        self.expr = expr
        
    def __eq__(self, other):
        if isinstance(other, self.__class__) and \
           self.var == other.var and \
           self.expr == other.expr:
            return True
        else:
            return False
        
        
class If(Node):
    
    def __init__(self, condition, result, elifs, else_):
        super(If, self).__init__()
        self.condition = condition
        self.result = result
        self.elifs = elifs
        self.else_ = else_
        
class Select(Node):
    
    def __init__(self, expr, cases):
        super(Select, self).__init__()
        self.expr = expr
        self.cases = cases

