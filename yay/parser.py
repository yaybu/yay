
from ply import yacc

from lexer import Lexer
from . import nodes

tokens = Lexer.tokens

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
    
def p_node_template(p):
    'node : BLOCK TEMPLATE END'
    p[0] = nodes.Jinja(p[2][1])
    
def p_node_extend(p):
    'node : EXTEND node'
    p[0] = nodes.Append(p[2])
    
def p_dict_key_node(p):
    'dict : KEY node'
    p[0] = [(p[1], p[2])]
    
def p_dict_dict_dict(p):
    'dict : dict dict'
    p[1].extend(p[2])
    p[0] = p[1]

def p_dict_emptydict(p):
    'dict : EMPTYDICT'
    p[0] = []
    
def p_list_listitem_node(p):
    'list : LISTITEM node'
    p[0] = [p[2]]
    
def p_list_list_list(p):
    'list : list list'
    p[1].extend(p[2])
    p[0] = p[1]
    
def p_list_emptylist(p):
    'list : EMPTYLIST'
    p[0] = []
    
parser = yacc.yacc()
