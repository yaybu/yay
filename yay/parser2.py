
from . import lexer

import types

class ParseError(Exception):
    pass

class Temp(lexer.Token):
    pass

class Parser(object):
    
    def __init__(self, lexerClass=lexer.Lexer):
        self.lexer = lexerClass()
        self.stack = []
    
    def input(self, text):
        self.lexer.input(text)
        self.lexer.done()
        
    def parse(self):
        for token in self.lexer.tokens():
            self.stack.append(token)
        data = {}
        while len(self.stack) > 1:
            key, value = self.reduce()
            data[key] = value
        return data
    
    def print_stack(self):
        for i in self.stack:
            print repr(i)
        print
                
    def reduce(self):
        endblock = self.stack.pop()
        if isinstance(self.stack[-1], lexer.VALUE):
            value = self.stack.pop()
            key = self.stack.pop()
            return key.value, value.value
        elif isinstance(self.stack[-1], lexer.LISTVALUE):
            l = []
            while isinstance(self.stack[-1], lexer.LISTVALUE):
                value = self.stack.pop()
                l.insert(0, value.value)
            key = self.stack.pop()
            return key.value, l
        elif isinstance(self.stack[-1], lexer.ENDBLOCK):
            d = {}
            while isinstance(self.stack[-1], lexer.ENDBLOCK):
                key, value = self.reduce()
                d[key] = value
            key = self.stack.pop()
            return key.value, d
        else:
            raise ParseError("buh")

