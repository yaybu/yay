



# Some of this code is (amusingly) taken from "lolpython"
# I am indebted to Andrew Dalke, author of lolpython, for the whitespace filters in particular
# the original copyright statement from lolpython follows
#
# Written by Andrew Dalke <dalke@dalkescientific.com>
# Dalke Scientific Software, LLC
# 1 June 2007, Gothenburg, Sweden
# 
# This software is in the public domain.  For details see:
#   http://creativecommons.org/licenses/publicdomain/



from ply import lex

# literals are checked last, after all of the other rules

literals = [
    '+', '-', '*', '/', '%', '&', '|', '^', '~', '<', '>',
    '(', ')', '[', ']', '{', '}', '@', ',', ':', '.', '`',
    '=', ';'
]

tokens = (
    'INDENT',
    'CONFIGURE',
    'DEDENT',
    'EMPTYDICT',
    'EMPTYLIST',
    'EXTEND',
    'KEY',
    'LDBRACE',
    'LISTITEM',
    'RDBRACE',
    'SCALAR',
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

t_LSHIFT = '<<'
t_RSHIFT = '>>'
t_LE = '<='
t_GE = '>='
t_EQ = '=='
t_NE = '!='
t_GTLT = '<>'
t_ELLIPSIS = r'\.\.\.'
t_POW = '\*\*'
t_FLOOR_DIVIDE = '//'

# Literals

def t_STRING(t):
    t.value = eval(t.value)
    return t

# just too complicated to put literally in a docstring
t_STRING.__doc__ =  (r"""
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

t_INTEGER = r"""
(?<![\w.])               #Start of string or non-alpha non-decimal point
    0[X][0-9A-F]+L?|     #Hexadecimal
    0[O][0-7]+L?|        #Octal
    0[B][01]+L?|         #Binary
    [1-9]\d*L?           #Decimal/Long Decimal, will not match 0____
(?![\w.])                #End of string or non-alpha non-decimal point
"""

t_FLOAT = r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]\d+)?)'

# Keywords

reserved = {
    'and': 'AND',
    'call': 'CALL',
    'create': 'CREATE',
    'else': 'ELSE',
    'if': 'IF',
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

# Identifiers

def t_IDENTIFIER(t):
    """[A-Za-z_][A-Za-z0-9_]*"""
    # check for reserved words
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t


def t_WS(t):
    r' [ ]+ '
    if t.lexer.at_line_start and not t.lexer.paren_stack:
        return t   

# Don't generate newline tokens when inside of parens
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.type = "NEWLINE"
    return t

def t_error(t):
    raise SyntaxError("Unknown symbol %r" % (t.value[0],))


# I implemented INDENT / DEDENT generation as a post-processing filter

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

def track_tokens_filter(lexer, tokens):
    # need to do some magic indent stuff
    lexer.at_line_start = at_line_start = True
    indent = NO_INDENT
    for token in tokens:
        
        token.at_line_start = at_line_start
        
        if token.type == ':':
            at_line_start = False
            indent = MAY_INDENT
            token.must_indent = False
            
        elif token.type == "NEWLINE":
            at_line_start = True
            if indent == MAY_INDENT:
                indent = MUST_INDENT
            token.must_indent = False
        
        elif token.type == "WS":
            assert token.at_line_start == True
            at_line_start = True
            token.must_indent = False
            
        else:
            # a real token. only indent after COLON NEWLINE
            if indent == MUST_INDENT:
                token.must_indent = True
            else:
                token.must_indent = False
            at_line_start = False
            
            indent = NO_INDENT
            
        yield token
        lexer.at_line_start = at_line_start

def _new_token(type, lineno):
    tok = lex.LexToken()
    tok.type = type
    tok.value = None
    tok.lineno = lineno
    tok.lexpos = -1
    return tok

def INDENT(lineno):
    return _new_token("INDENT", lineno)

def DEDENT(lineno):
    return _new_token("DEDENT", lineno)


def indentation_filter(tokens):
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
                yield INDENT(token.lineno)
            else:
                # back up, but only if it matches a previous level
                try:
                    i = levels.index(depth)
                except ValueError:
                    raise IndentationError("inconsistent indentation")
                for _ in range(i+1, len(levels)):
                    yield DEDENT(token.lineno)
                    levels.pop()
        yield token

    # dedent the remaining levels

    if len(levels) > 1:
        assert token is not None
        for _ in range(1, len(levels)):
            yield DEDENT(token.lineno)

def token_filter(lexer, add_endmarker = True):
    token = None
    tokens = iter(lexer.token, None)
    tokens = track_tokens_filter(lexer, tokens)
    for token in indentation_filter(tokens):
        yield token


class Lexer(object):

    def __init__(self, debug=0, optimize=0, lextab='lextab', reflags=0):
        self.lexer = lex.lex(debug=debug, optimize=optimize,
                             lextab=lextab, reflags=reflags)
        self.token_stream = None

    def input(self, s, add_endmarker=True):
        self.lexer.paren_stack = []
        self.lexer.input(s)
        self.token_stream = token_filter(self.lexer, add_endmarker)

    def token(self):
        try:
            return self.token_stream.next()
        except StopIteration:
            return None

    def __iter__(self):
        while True:
            yield self.token_stream.next()
