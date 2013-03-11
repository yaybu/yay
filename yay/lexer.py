# Copyright 2012 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" Lexing Yay 3 """

# Some of this code is (amusingly) taken from "lolpython" I am indebted to
# Andrew Dalke, author of lolpython, for the whitespace filters in particular
# the original copyright statement from lolpython follows

# Written by Andrew Dalke <dalke@dalkescientific.com>
# Dalke Scientific Software, LLC
# 1 June 2007, Gothenburg, Sweden
#
# This software is in the public domain.  For details see:
#   http://creativecommons.org/licenses/publicdomain/

import os
from ply import lex

class Lexer(object):

    def __init__(self, debug=0, optimize=0, lextab='lextab', reflags=0):
        self.lexer = lex.lex(module=self, debug=debug, optimize=optimize,
                             lextab=lextab, reflags=reflags,
                             outputdir=os.path.dirname(__file__))
        self.token_stream = None

    def input(self, s, add_endmarker=True):
        self.lexer.input(s)
        self.token_stream = self.token_filter(add_endmarker)

    def token(self):
        try:
            return self.token_stream.next()
        except StopIteration:
            return None

    def __iter__(self):
        while True:
            yield self.token_stream.next()

    states = (
        ('value', 'exclusive'),
        ('listvalue', 'exclusive'),
        ('template', 'exclusive'),
        ('command', 'exclusive'),
    )

    # literals are checked last, after all of the other rules

    literals = [
        '+', '-', '*', '/', '%', '&', '|', '^', '~', '<', '>',
        '(', ')', '[', ']', '{', '}', '@', ',', ':', '.', '`',
        '=', ';'
    ]

    tokens = (
        'PERCENT',
        'HYPHEN',
        'COMMENT',
        'INDENT',
        'CONFIGURE',
        'DEDENT',
        'EMPTYDICT',
        'EMPTYLIST',
        'EXTEND',
        'KEY',
        'LDBRACE',
        'RDBRACE',
        'VALUE',
        'IDENTIFIER',
        'STRING',
        'INTEGER',
        'FLOAT',
        'ELIF',
        'SELECT',
        'AND',
        'CALL',
        'CREATE',
        'ELSE',
        'IF',
        'IS',
        'FOR',
        'IN',
        'INCLUDE',
        'LAMBDA',
        'MACRO',
        'NOT',
        'OR',
        'SEARCH',
        'SET',
        'LSHIFT',
        'RSHIFT',
        'LE',
        'GE',
        'EQ',
        'NE',
        'GTLT',
        'ELLIPSIS',
        'POW',
        'FLOOR_DIVIDE',
        'WS',
        'NEWLINE',
    )

    t_command_template_LSHIFT = '<<'
    t_command_template_RSHIFT = '>>'
    t_command_template_LE = '<='
    t_command_template_GE = '>='
    t_command_template_EQ = '=='
    t_command_template_NE = '!='
    t_command_template_GTLT = '<>'
    t_command_template_ELLIPSIS = r'\.\.\.'
    t_command_template_POW = '\*\*'
    t_command_template_FLOOR_DIVIDE = '//'

    def t_template_RDBRACE(self, t):
        """}}"""
        t.lexer.begin('value')
        return t

    # Literals

    # just too complicated to put literally in a docstring
    string_expr =  (r"""
                         [uU]?[rR]?
                         (?:              # Single-quote (') strings
                         '''(?:                 # Triple-quoted can contain...
                         [^']               | # a non-quote
                         \\'                | # a backslashed quote
                         '{1,2}(?!')          # one or two quotes
                         )*''' |
                         '(?:                   # Non-triple quoted can contain...
                         [^']                | # a non-quote
                         \\'                   # a backslashded quote
                         )*'(?!') | """+
                                       r'''               # Double-quote (") strings
                                       """(?:                 # Triple-quoted can contain...
                                       [^"]               | # a non-quote
                                       \\"                | # a backslashed single
                                       "{1,2}(?!")          # one or two quotes
                                       )*""" |
                                       "(?:                   # Non-triple quoted can contain...
                                       [^"]                | # a non-quote
                                       \\"                   # a backslashed quote
                                       )*"(?!")
                                       )''')

    @lex.TOKEN(string_expr)
    def t_command_template_STRING(self, t):
        t.value = eval(t.value)
        return t

    def t_command_template_INTEGER(self, t):
        r"""
        (?<![\w.])               #Start of string or non-alpha non-decimal point
            0[X][0-9A-F]+L?|     #Hexadecimal
            0[O][0-7]+L?|        #Octal
            0[B][01]+L?|         #Binary
            [1-9]\d*L?           #Decimal/Long Decimal, will not match 0____
        (?![\w.])                #End of string or non-alpha non-decimal point
        """
        t.value = eval(t.value)
        return t

    def t_command_template_FLOAT(self, t):
        r'(\d+(?:\.\d+)?(?:[eE][+-]\d+)?)'
        t.value = eval(t.value)
        return t

    t_ANY_COMMENT = r"""\#[^\n]*"""

    # Keywords

    reserved = {
        'and': 'AND',
        'call': 'CALL',
        'create': 'CREATE',
        'else': 'ELSE',
        'if': 'IF',
        'elif': 'ELIF',
        'is': 'IS',
        'for': 'FOR',
        'in': 'IN',
        'include': 'INCLUDE',
        'lambda': 'LAMBDA',
        'macro': 'MACRO',
        'not': 'NOT',
        'or': 'OR',
        'search': 'SEARCH',
        'set': 'SET',
        'extend': 'EXTEND',
        'configure': 'CONFIGURE',
    }

    t_INITIAL_EXTEND = "extend"
    t_INITIAL_CONFIGURE = "configure"

    def t_INITIAL_listvalue_KEY(self, t):
        """[^:\n ]+:[ \t]*"""
        t.value = t.value.split(":", 1)[0]
        t.lexer.begin('value')
        return t

    def t_INITIAL_HYPHEN(self, t):
        """-[ \t]*"""
        t.value = '-'
        t.lexer.begin('listvalue')
        return t

    def t_INITIAL_PERCENT(self, t):
        """%[ \t]*"""
        t.value = '%'
        t.lexer.begin("command")
        return t

    def t_value_listvalue_EMPTYDICT(self, t):
        """{}"""
        t.lexer.begin("INITIAL")
        return t

    def t_value_listvalue_EMPTYLIST(self, t):
        """\[\]"""
        t.lexer.begin("INITIAL")
        return t

    def t_value_listvalue_LDBRACE(self, t):
        """{{"""
        t.lexer.begin("template")
        return t

    def t_value_listvalue_VALUE(self, t):
        """[^\{\n]+"""
        return t

    def t_command_template_IDENTIFIER(self, t):
        """[A-Za-z_][A-Za-z0-9_]*"""
        # check for reserved words
        t.type = self.reserved.get(t.value, 'IDENTIFIER')
        return t

    def t_ANY_WS(self, t):
        r' [ ]+ '
        if self.at_line_start:
            return t

    def t_ANY_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        t.type = "NEWLINE"
        t.lexer.begin("INITIAL")
        return t

    def t_ANY_error(self, t):
        raise SyntaxError("Unknown symbol %r at line %d" % (t.value[0], t.lineno))


    # The original lex token stream contains WS and NEWLINE characters.
    # WS will only occur before any other tokens on a line.

    # I have three filters.  One tags tokens by adding two attributes.
    # "must_indent" is True if the token must be indented from the
    # previous code.  The other is "at_line_start" which is True for WS
    # and the first non-WS/non-NEWLINE on a line.  It flags the check so
    # see if the new line has changed indication level.

    # yay's syntax has three INDENT states
    # 0) within a command block or a list, so no need to indent
    # 1) within a dictionary, or after a colon in command mode so we may indent, or not
    # 2) a colon followed by a newline, so we must indent
    NO_INDENT = 0
    MAY_INDENT = 1
    MUST_INDENT = 2

    def track_tokens_filter(self, tokens):
        # need to do some magic indent stuff
        self.at_line_start = at_line_start = True
        indent = self.NO_INDENT
        for token in tokens:

            token.at_line_start = at_line_start

            if token.type == ':':
                at_line_start = False
                indent = self.MAY_INDENT
                token.must_indent = False

            elif token.type == "NEWLINE":
                at_line_start = True
                if indent == self.MAY_INDENT:
                    indent = self.MUST_INDENT
                token.must_indent = False

            elif token.type == "WS":
                assert token.at_line_start == True
                at_line_start = True
                token.must_indent = False

            else:
                # a real token. only indent after COLON NEWLINE
                if indent == self.MUST_INDENT:
                    token.must_indent = True
                else:
                    token.must_indent = False
                at_line_start = False

                indent = self.NO_INDENT

            yield token
            self.at_line_start = at_line_start

    def _new_token(self, type, lineno):
        tok = lex.LexToken()
        tok.type = type
        tok.value = None
        tok.lineno = lineno
        tok.lexpos = -1
        return tok

    def INDENT(self, lineno):
        return self._new_token("INDENT", lineno)

    def DEDENT(self, lineno):
        return self._new_token("DEDENT", lineno)

    def indentation_filter(self, tokens):
        """ Track the indentation level and emit the right INDENT / DEDENT events. """
        levels = [0] # first level is determined by first token
        token = None
        depth = None
        prev_was_ws = False
        for token in tokens:
            if depth is None:
                # first ever token other than newline
                if token.type == 'WS':
                    depth = len(token.value)
                    levels = [depth]
                elif token.type == 'NEWLINE':
                    pass
                else:
                    depth = 0

            if token.type == 'WS':
                assert depth == levels[0]
                depth = len(token.value)
                prev_was_ws = True
                continue
            elif token.type == 'NEWLINE':
                if depth is not None:
                    depth = levels[0]
                if prev_was_ws or token.at_line_start:
                    continue
                yield token
                continue
            prev_was_ws = False
            if token.must_indent:
                if not (depth > levels[-1]):
                    raise IndentationError("expected and indented block")
                levels.append(depth)
                yield INDENT(token.lineno)
            elif token.at_line_start:
                if depth == levels[-1]:
                    # at the same level
                    pass
                elif depth > levels[-1]:
                    #raise IndentationError("indentation increase but not in new block")
                    levels.append(depth)
                    yield self.INDENT(token.lineno)
                else:
                    # back up, but only if it matches a previous level
                    try:
                        i = levels.index(depth)
                    except ValueError:
                        raise IndentationError("inconsistent indentation")
                    for _ in range(i+1, len(levels)):
                        yield self.DEDENT(token.lineno)
                        levels.pop()
            yield token

        # dedent the remaining levels

        if len(levels) > 1:
            assert token is not None
            for _ in range(1, len(levels)):
                yield self.DEDENT(token.lineno)

    def token_filter(self, add_endmarker = True):
        token = None
        tokens = iter(self.lexer.token, None)
        tokens = self.track_tokens_filter(tokens)
        for token in self.indentation_filter(tokens):
            yield token

