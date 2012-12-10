
from ply import yacc

from lexer import Lexer
from . import nodes

tokens = Lexer.tokens

start = 'node'

def p_include(p):
    'include : PERCENT INCLUDE expr'
    p[0] = nodes.Include(p[3])
    
def p_consume_include(p):
    'dict : dict include'
    # 

def p_expr_scalar(p):
    '''expr : STRING
            | INTEGER
            | FLOAT
            | function
            | VAR
    '''
    p[0] = p[1]
    
def p_expr_operator(p):
    'expr : expr OP expr'
    p[0] = nodes.Operator(p[2], p[1], p[3])
    
def p_expr_comparison(p):
    'expr : expr CMP expr'
    p[0] = nodes.Comparison(p[2], p[1], p[3])

def p_expression_list(p):
    '''expression_list : expression'''
    p[0] = [p[1]]
    
def p_expression_list_cont(p):
    'expression_list : expression_list COMMA expression'
    p[0] = p[1]
    p[0].append(p[3])
    
def p_function(p):
    'function : FUNCTION LPAREN expression_list RPAREN'
    p[0] = nodes.Function(p[1], p[3])

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
