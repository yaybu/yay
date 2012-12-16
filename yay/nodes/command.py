
from yay.nodes import Node

class Include(Node):
    
    def __init__(self, expr):
        super(Include, self).__init__()
        self.expr = expr
        
    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.expr == other.expr

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
        
    def __repr__(self):
        return "<Set %r = %r>" % (self.var, self.expr)
        
        
class If(Node):
    
    def __init__(self, condition, result, elifs=None, else_=None):
        super(If, self).__init__()
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
        
class Select(Node):
    
    def __init__(self, expr, cases):
        super(Select, self).__init__()
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
        
class For(Node):
    
    def __init__(self, target, in_clause, node, if_clause=None):
        self.target = target
        self.if_clause = if_clause
        self.in_clause = in_clause
        self.node = node