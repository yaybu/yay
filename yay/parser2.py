from ply import yacc as yacc
from yay.lexer import tokens

parsed = {}
current = None

def p_bare_key(p):
    'barekey: WS* TERM COLON WS* CR'
    
    

def p_list_item(p):
    'listitem: WS DASH WS expression CR'
    stack_top().append(p[3])

def p_expression_inline(p):
    'expression : TERM COLON expression CR'
    p[0] = {}
    p[0][p[1]] = p[3]
    push_key(p[0])
    
def p_emptyline(p):
    'empty : CR WS* CR'
    pop_key()
    
def p_continuation(p):
    pass

    
    



