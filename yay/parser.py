

from ply import yacc

from lexer import Lexer
from . import nodes

tokens = Lexer.tokens


########## EXPRESSIONS
## http://docs.python.org/2/reference/expressions.html

def p_atom(p):
    '''
    atom : IDENTIFIER
         | LITERAL
         | enclosure
    '''
    
def p_enclosure(p):
    '''
    enclosure : parenth_form 
              | list_display
              | generator_expression
              | dict_display
              | set_display
              | string_conversion
    '''

def p_parent_form(p):
    '''
    parenth_form : "(" ")"
                 | "(" expression_list ")"
    '''
    
def p_list_display(p):
    '''
    list_display : "[" "]"
                 | "[" expression_list "]"
                 | "[" list_comprehension "]"
    '''
    
def p_list_comprehension(p):
    '''
    list_comprehension : expression list_for
    '''
    
def p_list_for(p):
    '''
    list_for : FOR target_list IN old_expression_list
             | FOR target_list IN old_expression_list list_iter
    '''
    
def p_old_expression_list(p):
    '''
    old_expression_list : old_expression
                        | old_expression_list "," old_expression
                        | old_expression_list "," old_expression ","
    '''
    
def p_old_expression(p):
    '''
    old_expression : or_test 
                   | old_lambda_form
    '''
    
def p_list_iter(p):
    '''
    list_iter : list_for
              | list_if
    '''
    
def p_list_if(p):
    '''
    list_if : IF old_expression
            | IF old_expression list_iter
    '''
    
def p_comprehension(p):
    '''
    comprehension : expression comp_for
    '''
    
def p_comp_for(p):
    '''
    comp_for : FOR target_list IN or_test
             | FOR target_list IN or_test comp_iter
    '''
    
def p_comp_iter(p):
    '''
    comp_iter : comp_for
              | comp_if
    '''
    
def p_comp_if(p):
    '''
    comp_if : IF expression
            | IF expression comp_iter
    '''
    
    # expression is actually "expression_nocond" in the grammar
    # i do not know what this means
    # http://docs.python.org/2/reference/expressions.html#displays-for-sets-and-dictionaries
    
def p_generator_expression(p):
    '''
    generator_expression : "(" expression comp_for ")"
    '''
    
def p_dict_display(p):
    '''
    dict_display : "{" "}"
                 | "{" key_datum_list "}"
                 | "{" dict_comprehension "}"
    '''
    
def p_key_datum_list(p):
    '''
    key_datum_list : key_datum
                   | key_datum_list "," key_datum
    '''

def p_key_datum(p):
    '''
    key_datum : expression ":" expression
    '''

def p_dict_comprehension(p):
    '''
    dict_comprehension : expression ":" expression comp_for
    '''
    
def p_set_display(p):
    '''
    set_display : "{" expression_list "}"
                | "{" comprehension "}"
    '''
    
def p_string_conversion(p):
    '''
    string_conversion : "`" expression_list "`"
    '''
    
def p_primary(p):
    '''
    primary : atom
            | attributeref
            | subscription
            | slicing
            | call
    '''
    
def p_attributeref(p):
    '''
    attributeref : primary "." IDENTIFIER
    '''
    
def p_subscription(p):
    '''
    subscription : primary "[" expression_list "]"
    '''
    
def p_slicing(p):
    '''
    slicing : simple_slicing
            | extended_slicing
    '''
    
def p_simple_slicing(p):
    '''
    simple_slicing : primary "[" short_slice "]"
    '''
    
def p_extended_slicing(p):
    '''
    extended_slicing : primary "[" slice_list "]"
    '''
    
def p_slice_list(p):
    '''
    slice_list : slice_item
               | slice_list "," slice_item
               | slice_list "," slice_item ","
    '''
    
def p_slice_item(p):
    '''
    slice_item : proper_slice
               | ELLIPSIS
    '''
    # removed expression as a production due to reduce/reduce conflict
    # should really be there
    
def p_proper_slice(p):
    '''
    proper_slice : short_slice
                 | long_slice
    '''
    
def p_short_slice(p):
    '''
    short_slice : lower_bound ":"
                | ":" upper_bound
                | lower_bound ":" upper_bound
    '''
    
def p_long_slice(p):
    '''
    long_slice : short_slice ":"
               | short_slice ":" stride
    '''
    
def p_lower_bound(p):
    '''
    lower_bound : expression
    '''
    
def p_upper_bound(p):
    '''
    upper_bound : expression
    '''
    
def p_stride(p):
    '''
    stride : expression
    '''

def p_call(p):
    '''
    call : primary "(" ")"
         | primary "(" argument_list ")"
         | primary "(" argument_list "," ")"
    '''
    # some other stuff in here for genexpr_for that i don't grok
    
def p_argument_list(p):
    '''
    argument_list : positional_arguments
                  | positional_arguments "," keyword_arguments
    '''
    # ignore all the * and ** stuff, don't think relevant
    
def p_positional_arguments(p):
    '''
    positional_arguments : expression
                         | positional_arguments "," expression
    '''
    
def p_keyword_arguments(p):
    '''
    keyword_arguments : keyword_item
                      | keyword_arguments "," keyword_item
    '''
    
def p_keyword_item(p):
    '''
    keyword_item : IDENTIFIER "=" expression
    '''
    
def p_power(p):
    '''
    power : primary
          | primary POW u_expr
    '''

def p_u_expr(p):
    '''
    u_expr : power
           | "-" u_expr
           | "+" u_expr
           | "~" u_expr
    '''
    
def p_m_expr(p):
    '''
    m_expr : u_expr
           | m_expr "*" u_expr
           | m_expr FLOOR_DIVIDE u_expr
           | m_expr "/" u_expr
           | m_expr "%" u_expr
    '''
    
def p_a_expr(p):
    '''
    a_expr : m_expr
           | a_expr "+" m_expr
           | a_expr "-" m_expr
    '''
    
def p_shift_expr(p):
    '''
    shift_expr : a_expr
               | shift_expr LSHIFT a_expr
               | shift_expr RSHIFT a_expr
    '''
    
def p_and_expr(p):
    '''
    and_expr : shift_expr
             | and_expr "&" shift_expr
    '''
    
def p_xor_expr(p):
    '''
    xor_expr : and_expr
             | xor_expr "^" and_expr
    '''
    
def p_or_expr(p):
    '''
    or_expr : xor_expr
            | or_expr "|" xor_expr
    '''
    
def p_comparison(p):
    '''
    comparison : or_expr comp_operator or_expr
               | comparison comp_operator or_expr
    '''
    
def p_comp_operator(p):
    '''
    comp_operator : "<"
                  | ">"
                  | EQ
                  | GE
                  | LE
                  | GTLT
                  | NE
                  | IS
                  | IS NOT
                  | NOT
                  | NOT IN
    '''
    
def p_or_test(p):
    '''
    or_test : and_test
            | or_test OR and_test
    '''
    
def p_and_test(p):
    '''
    and_test : not_test
             | and_test AND not_test
    '''
    
def p_not_test(p):
    '''
    not_test : comparison
             | NOT not_test
    '''
    
def p_conditional_expression(p):
    '''
    conditional_expression : or_test
                           | or_test IF or_test ELSE expression
    '''
    
def p_expression(p):
    '''
    expression : conditional_expression
               | lambda_form
    '''
    
def p_lambda_form(p):
    '''
    lambda_form : LAMBDA ":" expression
                | LAMBDA parameter_list ":" expression
    '''
    
def p_old_lambda_form(p):
    '''
    old_lambda_form : LAMBDA ":" expression
                    | LAMBDA parameter_list ":" old_expression
    '''

def p_expression_list(p):
    '''
    expression_list : expression
                    | expression_list "," expression
                    | expression_list "," expression ","
    '''

#### SIMPLE STATEMENTS
# http://docs.python.org/2/reference/simple_stmts.html

def p_target_list(p):
    '''
    target_list : target
                | target_list "," target
                | target_list "," target ","
    '''
    
def p_target(p):
    '''
    target : IDENTIFIER
           | attributeref
           | subscription
           | slicing
    '''

#### COMPOUND STATEMENTS
# http://docs.python.org/2/reference/compound_stmts.html

def p_parameter_list(p):
    '''
    parameter_list : defparameter
                   | parameter_list "," defparameter
                   | parameter_list "," defparameter ","
    '''
    
def p_defparameter(p):
    '''
    defparameter : parameter
                 | parameter "=" expression
    '''
    
def p_parameter(p):
    '''
    parameter : IDENTIFIER
              | "(" sublist ")"
    '''
    
def p_sublist(p):
    '''
    sublist : parameter
            | sublist "," parameter
            | sublist "," parameter ","
    '''

##############################




def p_node_scalar(p):
    'node : BLOCK SCALAR END'
    p[0] = nodes.Boxed(p[2])
    
def p_node_dict(p):
    'node : BLOCK dict END'
    m = nodes.Mapping()
    for key, value in p[2]:
        value.set_predecessor(m.get(key))
        m.set(key, value)
    p[0] = m
    
def p_node_list(p):
    'node : BLOCK list END'
    p[0] = nodes.Sequence(p[2])

def p_extend(p):
    'extend : EXTEND KEY node'
    p[0] = (p[2], nodes.Extend(p[3]))
    
def p_dict_extend(p):
    'dict : extend'
    p[0] = [(p[1][0], p[1][1])]
    
def p_dict_key_node(p):
    'dict : KEY node'
    p[0] = [(p[1], p[2])]
    
def p_dict_dict_dict(p):
    'dict : dict dict'
    p[1].extend(p[2])
    p[0] = p[1]

def p_dict_emptydict(p):
    'dict : EMPTYDICT'
    p[0] = nodes.Mapping()
    
def p_list_listitem_node(p):
    'list : LISTITEM node'
    p[0] = [p[2]]
    
def p_list_list_list(p):
    'list : list list'
    p[1].extend(p[2])
    p[0] = p[1]
    
def p_list_emptylist(p):
    'list : EMPTYLIST'
    p[0] = nodes.Sequence()
    
parser = yacc.yacc()

def parse(value):
    return parser.parse(value, lexer=Lexer())
