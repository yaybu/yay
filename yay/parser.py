
from .lexer import (Token, Lexer, 
                    BLOCK, END, 
                    TEMPLATE, SCALAR, LISTITEM, EMPTYLIST, EMPTYDICT,
                    KEY, EXTEND,
                    DIRECTIVE)
from . import nodes

import logging
import types

logger = logging.getLogger(__name__)

class ParseError(Exception):
    pass

class DICT(Token):
    
    """ A dictionary """

class LIST(Token):
    
    """ A list """

class NODE(Token):
    
    """ A value that has been turned into one of the node classes """

VALUE = (SCALAR, DICT, LIST, EMPTYDICT, EMPTYLIST, TEMPLATE)

class Parser(object):
    
    def __init__(self, lexer=None):
        self.lexer = Lexer() if lexer is None else lexer
        self.stack = []
    
    def input(self, text):
        logger.debug("Parsing >>>")
        logger.debug(text)
        logger.debug("<<< Parsing")
        self.lexer.input(text)
        self.lexer.done()
        
    def parse(self):
        for token in self.lexer.tokens():
            self.stack.append(token)
            logger.debug("+ %r" % self.stack)
            while self.reduce():
                logger.debug("- %r" % self.stack)
        if len(self.stack) > 1:
            raise ParseError("Stack not completely reduced: %r" % self.stack)
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
    
    def match_node(self):
        """ COMPLETE: BLOCK VALUE END """
        
        if self.matches(BLOCK, VALUE, END):
            t_block, t_value, t_end = self.pop(3)
            if isinstance(t_value, SCALAR):
                self.stack.append(NODE(nodes.Boxed(t_value.value)))
                return True
            if isinstance(t_value, DICT):
                m = nodes.Mapping()
                for key, value in t_value.value:
                    value.set_predecessor(m.get(key))
                    m.set(key, value)
                self.stack.append(NODE(m))
                return True
            if isinstance(t_value, LIST):
                self.stack.append(NODE(nodes.Sequence(t_value.value)))
                return True
            if isinstance(t_value, TEMPLATE):
                self.stack.append(NODE(nodes.Jinja(t_value.value[1])))
                return True

    def match_adaptor(self):
        """ NODE := EXTEND NODE """
        if self.matches(EXTEND, NODE):
            t_extend, t_node = self.pop(2)
            self.stack.append(NODE(nodes.Append(t_node.value)))
            return True
        return False

    def match_dict(self):
        """ DICT := KEY NODE
                  | DICT DICT
                  | EMPTYDICT
        """
        if self.matches(KEY, NODE):
            t_key, t_node = self.pop(2)
            self.stack.append(DICT([(t_key.value, t_node.value)]))
            return True
        if self.matches(DICT, DICT):
            t_1, t_2 = self.pop(2)
            t_1.value.extend(t_2.value)
            self.stack.append(t_1)
            return True
        if self.matches(EMPTYDICT):
            t_d = self.pop(1)
            self.stack.append(DICT([]))
            return True
        return False
        
    def match_list(self):
        """ LIST := LISTITEM NODE
                  | LIST LIST
                  | EMPTYLIST
        """
        if self.matches(LISTITEM, NODE):
            t_listitem, t_node = self.pop(2)
            self.stack.append(LIST([t_node.value]))
            return True
        if self.matches(LIST, LIST):
            t_1, t_2 = self.pop(2)
            t_1.value.extend(t_2.value)
            self.stack.append(t_1)
            return True
        if self.matches(EMPTYLIST):
            t_l = self.pop(1)
            self.stack.append(LIST([]))
            return True
        return False
        
    def reduce(self):
        """ Examine the end of the stack for matches with productions.
        Extract the matching elements and replace them with the result of the
        production. """

        if self.match_node():
            return True
        if self.match_adaptor():
            return True
        if self.match_dict():
            return True
        if self.match_list():
            return True
        return False
            
