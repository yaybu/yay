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
    def __init__(self, positional_arguments, keyword_arguments=None):
        self.positional_arguments = positional_arguments
        self.keyword_arguments = keyword_arguments
      
class PositionalArguments(AST):
    def __init__(self, *expressions):
        self.positional_arguments = list(expressions)
        
    def append(self, expression):
        self.positional_arguments.append(expression)
        
class KeywordArguments(AST):
    def __init__(self, *keyword_items):
        self.keyword_arguments = list(keyword_items)
        
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
        
class YayList(AST):
    def __init__(self, *items):
        self.value = list(items)
        
    def append(self, item):
        self.value.append(item)
        
class YayDict(AST):
    
    """ A dictionary in yay may redefine items, so update merely appends. The
    value is a list of 2-tuples """
    
    def __init__(self, value=None):
        if value is None:
            self.value = []
        else:
            self.value = value
        
    def update(self, l):
        self.value.extend(l)
            
    def __iter__(self):
        return iter(self.value)
        
class YayExtend(AST):
    def __init__(self, key, value):
        self.value = {key: value}
        
class YayScalar(AST):
    def __init__(self, value):
        self.value = value

class Stanzas(AST):
    def __init__(self, *stanzas):
        self.value = list(stanzas)
        
    def append(self, stanza):
        self.value.append(stanza)

class Directives(AST):
    def __init__(self, *directives):
        self.value = list(directives)
        
    def append(self, directive):
        self.value.append(directive)
        
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
        
class For(AST):
    
    def __init__(self, target, in_clause, node, if_clause=None):
        self.target = target
        self.if_clause = if_clause
        self.in_clause = in_clause
        self.node = node        

class Template(AST):
    def __init__(self, *value):
        self.value = list(value)
        
    def append(self, value):
        self.value.append(value)
        
    def prepend(self, value):
        self.value.insert(0, value)