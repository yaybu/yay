
from .lexer import Token, Lexer, BLOCK, END, SCALAR, LISTITEM, KEY, EMPTYLIST, EMPTYDICT

from . import nodes

import types

class ParseError(Exception):
    pass

class DICT(Token):
    pass

class KVP(Token):
    pass

class LIST(Token):
    pass

VALUE = (KVP, SCALAR, DICT, LIST, EMPTYDICT, EMPTYLIST)

class Parser(object):
    
    def __init__(self, lexer=None):
        self.lexer = Lexer() if lexer is None else lexer
        self.stack = []
    
    def input(self, text):
        self.lexer.input(text)
        self.lexer.done()
        print "==========+"
        
    def parse(self):
        for token in self.lexer.tokens():
            self.stack.append(token)
            print self.stack
            while self.reduce():
                print self.stack
                pass
        return self.stack[0].value

    def matches(self, *match):
        tokens = len(match)
        if len(self.stack) < tokens:
            return False
        for pos, token in enumerate(match):
            offset = -tokens+pos # 1 token, 1 pos = -1
            if not isinstance(self.stack[offset], token):
                return False
        return True
    
    def pop(self, number):
        def _():
            for i in range(number):
                yield self.stack.pop()
        return reversed(list(_()))

    def value(self, token):
        if isinstance(token, SCALAR):
            value = nodes.Boxed(token.value)
        else:
            value = token.value
        return value
    
    def match_kvp(self):
        """ KVP := KEY BLOCK VALUE END """
        
        if self.matches(KEY, BLOCK, VALUE, END):
            t_key, t_block, t_value, t_end = self.pop(4)
            self.stack.append(KVP((t_key.value, self.value(t_value))))
            return True
    
    def match_dict(self):
        """ DICT := BLOCK KVP
                  | DICT KVP
                  | DICT END
                  | EMPTYDICT
        """
        if self.matches(BLOCK, KVP):
            t_block, t_kvp = self.pop(2)
            n = nodes.Mapping()
            n.set(*t_kvp.value)
            self.stack.append(DICT(n))
            return True
        if self.matches(DICT, KVP):
            t_dict, t_kvp = self.pop(2)
            t_dict.value.set(*t_kvp.value)
            self.stack.append(t_dict)
            return True
        if self.
        if self.matches(EMPTYDICT):
            t_d = self.pop(1)
            self.stack.append(DICT(nodes.Mapping()))
            return True
        return False
        
    def match_list(self):
        """ LIST := LISTITEM BLOCK VALUE END
                  | LIST LIST
                  | EMPTYLIST
        """
        if self.matches(LISTITEM, BLOCK, VALUE, END):
            t_listitem, t_block, t_value, t_end = self.pop(4)
            node = nodes.Sequence([self.value(t_value)])
            self.stack.append(LIST(node))
            return True
        if self.matches(LIST, LIST):
            t_1, t_2 = self.pop(2)
            t_1.value.extend(t_2.value)
            self.stack.append(t_1)
            return True
        if self.matches(EMPTYLIST):
            t_l = self.pop(1)
            self.stack.append(LIST(nodes.Sequence()))
            return True
        return False
        
    def log(self, s):
        print s
            
    def reduce(self):
        """ Examine the end of the stack for matches with productions.
        Extract the matching elements and replace them with the result of the
        production. """

        if self.match_kvp():
            return True
        if self.match_dict():
            return True
        if self.match_list():
            return True
        return False
            