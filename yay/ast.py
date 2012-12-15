class AST(object):
    pass

class ParentForm(AST):
    def __init__(self, expression_list=None):
        self.value = expression_list
        
class ExpressionList(AST):
    def __init__(self, *expression_list):
        self.value = expression_list
        
    def append(self, expression):
        self.value.append(expression)
        
        
class Power(AST):
    def __init__(self, primary, power=None):
        self.primary = primary
        self.power = power
        
class UnaryMinus(AST):
    """ The unary - (minus) operator yields the negation of its numeric
    argument. """
    
    def __init__(self, value):
        self.value = value
        
class Invert(AST):
    """ The unary ~ (invert) operator yields the bitwise inversion of its
    plain or long integer argument. The bitwise inversion of x is defined as
    -(x+1). It only applies to integral numbers. """
    def __init__(self, value):
        self.value = value
        
class Expr(AST):
    def __init__(self, lhs, rhs, operator):
        self.lhs = lhs
        self.rhs = rhs
        self.operator = operator
        
class Not(AST):
    def __init__(self, value):
        self.value = value

class ConditionalExpression(AST):
    def __init__(self, or_test, if_clause, else_clause):
        self.or_test = or_test
        self.if_clause = if_clause
        self.else_clause = else_clause
        
        