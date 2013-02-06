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
    'LITERAL_STRING',
    'LITERAL_INTEGER',
    'LITERAL_FLOAT',
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

# Long literals. We match these first

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

t_LITERAL_STRING =  (r"""
    [uU]?[rR]?
      (?:              # Single-quote (') strings
      '''(?:                 # Tripple-quoted can contain...
          [^']               | # a non-quote
          \\'                | # a backslashed quote
          '{1,2}(?!')          # one or two quotes
        )*''' |
      '(?:                   # Non-tripple quoted can contain...
         [^']                | # a non-quote
         \\'                   # a backslashded quote
       )*'(?!') | """+
    r'''               # Double-quote (") strings
      """(?:                 # Tripple-quoted can contain...
          [^"]               | # a non-quote
          \\"                | # a backslashed single
          "{1,2}(?!")          # one or two quotes
        )*""" |
      "(?:                   # Non-tripple quoted can contain...
         [^"]                | # a non-quote
         \\"                   # a backslashded quote
       )*"(?!")
    )''')

t_LITERAL_INTEGER = r"""
(?<![\w.])               #Start of string or non-alpha non-decimal point
    0[X][0-9A-F]+L?|     #Hexadecimal
    0[O][0-7]+L?|        #Octal
    0[B][01]+L?|         #Binary
    [1-9]\d*L?           #Decimal/Long Decimal, will not match 0____
(?![\w.])                #End of string or non-alpha non-decimal point
"""

t_LITERAL_FLOAT = r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]\d+)?)'

# Keywords

t_AND = 'and'
t_CALL = 'call'
t_CREATE = 'create'
t_ELSE = 'else'
t_IF = 'if'
t_IS = 'is'
t_FOR = 'for'
t_IN = 'in'
t_INCLUDE = 'include'
t_LAMBDA = 'lambda'
t_MACRO = 'macro'
t_NOT = 'not'
t_OR = 'or'
t_SEARCH = 'search'
t_SET = 'set'
t_EXTEND = 'extend'
t_CONFIGURE = 'configure'

# Identifiers

t_IDENTIFIER = "[A-Za-z_][A-Za-z0-9_]*"


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


def track_tokens_filter(lexer, tokens):
    # need to do some magic indent stuff
    for token in tokens:
        token.at_line_start = False
        token.must_indent = False
        yield token

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
    levels = [0]
    token = None
    depth = 0
    prev_was_ws = False
    for token in tokens:
        if token.type == 'WS':
            assert depth == 0
            depth = len(token.value)
            prev_was_ws = True
            continue
        elif token.type == 'NEWLINE':
            depth = 0
            if prev_was_ws or token.at_line_start:
                # ignore blank lines
                continue
            yield token
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
                raise IndentationError("indentation increase but not in new block")
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
        yield self.token_stream.next()