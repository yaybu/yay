
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
        
    def peek(self):
        return self.stack[-1]

    def reduce(self):
        endblock = self.stack.pop()
        if isinstance(self.peek(), lexer.VALUE):
            value = self.stack.pop()
            key = self.stack.pop()
            return key.value, value.value
        elif isinstance(self.peek(), (lexer.LISTVALUE, lexer.LISTKEY)):
            l = []
            while isinstance(self.peek(), (lexer.LISTVALUE, lexer.LISTKEY, lexer.ENDBLOCK)):
                if isinstance(self.peek(), lexer.LISTVALUE):
                    value = self.stack.pop()
                    l.insert(0, value.value)
                elif isinstance(self.peek(), lexer.ENDBLOCK):
                    key, value = self.reduce()
                    l.insert(0, {key: value})
            key = self.stack.pop()
            return key.value, l
        elif isinstance(self.peek(), lexer.ENDBLOCK):
            d = {}
            while isinstance(self.peek(), lexer.ENDBLOCK):
                key, value = self.reduce()
                d[key] = value
            key = self.stack.pop()
            return key.value, d
        else:
            raise ParseError("buh")

