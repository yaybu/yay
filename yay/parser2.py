
from .lexer import Token, Lexer, BLOCK, END, SCALAR, LISTITEM, KEY, EMPTYLIST, EMPTYDICT

import types

class ParseError(Exception):
    pass

class KVP(Token):
    pass

class DICT(Token):
    pass

class LIST(Token):
    pass

VALUE = (SCALAR, DICT, LIST, EMPTYDICT, EMPTYLIST)

class Parser(object):
    
    def __init__(self, lexer=None):
        self.lexer = Lexer() if lexer is None else lexer
        self.stack = []
    
    def input(self, text):
        self.lexer.input(text)
        self.lexer.done()
        
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

    def match_dict(self):
        """ DICT := KEY BLOCK VALUE END 
                  | DICT DICT
        """
        if self.matches(KEY, BLOCK, VALUE, END):
            t_key, t_block, t_value, t_end = self.pop(4)
            produces = DICT({t_key.value:t_value.value})
            self.stack.append(produces)
            return True
        if self.matches(DICT, DICT):
            t_1, t_2 = self.pop(2)
            t_1.value.update(t_2.value)
            self.stack.append(t_1)
            return True
        return False
        
    def match_list(self):
        """ LIST := LISTITEM BLOCK VALUE END
                  | LIST LIST
        """
        if self.matches(LISTITEM, BLOCK, VALUE, END):
            t_listitem, t_block, t_value, t_end = self.pop(4)
            produces = LIST([t_value.value])
            self.stack.append(produces)
            return True
        if self.matches(LIST, LIST):
            t_1, t_2 = self.pop(2)
            t_1.value.extend(t_2.value)
            self.stack.append(t_1)
            return True
        return False
        
    def log(self, s):
        print s
            
    def reduce(self):
        """ Examine the end of the stack for matches with productions.
        Extract the matching elements and replace them with the result of the
        production. """

        if self.match_dict():
            return True
        if self.match_list():
            return True
        return False
            