class AST(object):
    
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__dict__)
    
    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

class Identifier(AST):
    def __init__(self, identifier):
        self.identifier = identifier
        
class Literal(AST):
    def __init__(self, literal):
        self.literal = literal

class ParentForm(AST):
    def __init__(self, expression_list=None):
        self.expression_list = expression_list
        
class ExpressionList(AST):
    def __init__(self, *expressions):
        self.expression_list = list(expressions)
        
    def append(self, expression):
        self.expression_list.append(expression)
        
class Power(AST):
    def __init__(self, primary, power=None):
        self.primary = primary
        self.power = power
        
class UnaryMinus(AST):
    """ The unary - (minus) operator yields the negation of its numeric
    argument. """
    
    def __init__(self, u_expr):
        self.u_expr = u_expr
        
class Invert(AST):
    """ The unary ~ (invert) operator yields the bitwise inversion of its
    plain or long integer argument. The bitwise inversion of x is defined as
    -(x+1). It only applies to integral numbers. """
    def __init__(self, u_expr):
        self.u_expr = u_expr
        
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
        
class ListDisplay(AST):
    def __init__(self, expression_list=None):
        self.expression_list = expression_list

class DictDisplay(AST):
    
    def __init__(self, key_datum_list=None):
        self.key_datum_list = key_datum_list
        
class KeyDatumList(AST):
    
    def __init__(self, key_datum):
        self.value = [key_datum]
        
    def append(self, key_datum):
        self.value.append(key_datum)
        
class KeyDatum(AST):
    
    def __init__(self, key, value):
        self.key = key
        self.value = value
        
class AttributeRef(AST):
    def __init__(self, primary, identifier):
        self.primary = primary
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
    def __init__(self, primary, argument_list=None):
        self.primary = primary
        self.argument_list = argument_list
        
class ArgumentList(AST):
    def __init__(self, positional_arguments, keyword_arguments):
        self.positional_arguments = positional_arguments
        self.keyword_arguments = keyword_arguments
      
class PositionalArguments(AST):
    def __init__(self, expression):
        self.positional_arguments = [expression]
        
    def append(self, expression):
        self.positional_arguments.append(expression)
        
class KeywordArguments(AST):
    def __init__(self, keyword_item):
        self.keyword_arguments = [keyword_item]
        
    def append(self, keyword_item):
        self.keyword_arguments.append(keyword_item)
        
class KeywordItem(AST):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression
      
class TargetList(AST):
    def __init__(self, target):
        self.target_list = [target]
        
    def append(self, target):
        self.target_list.append(target)
        
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
        