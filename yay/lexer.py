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

import re

from .errors import LexerError

from ply import lex

PY_STRING_LITERAL_RE = (r"""
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

PY_IDENTIFER_RE = "[A-Za-z_][A-Za-z0-9_]*"

PY_INTEGER_RE = r"""
(?<![\w.])               #Start of string or non-alpha non-decimal point
    0[X][0-9A-F]+L?|     #Hexadecimal
    0[O][0-7]+L?|        #Octal
    0[B][01]+L?|         #Binary
    [1-9]\d*L?           #Decimal/Long Decimal, will not match 0____
(?![\w.])                #End of string or non-alpha non-decimal point
"""

PY_FLOAT_RE = r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]\d+)?)'

string_literal_re = re.compile(PY_STRING_LITERAL_RE, re.VERBOSE)
identifier_re = re.compile(PY_IDENTIFER_RE)
integer_re = re.compile(PY_INTEGER_RE, re.VERBOSE | re.IGNORECASE)
float_re = re.compile(PY_FLOAT_RE)

class LexToken(lex.LexToken):
    
    def __init__(self, name, value=None, lineno=0, lexpos=0, orig=None):
        self.type = name
        self.value = value
        self.lineno = lineno
        self.lexpos = lexpos
        self.orig = orig or value
    
    def __len__(self):
        return len(self.orig)
    
class Lexer(object):
    
    """ Leading significant whitespace lexing considered fugly. """
    
    literals = [
        '\+', '-', '\*', '/', '%', '&', '\|', '\^', '\~', '<', '>',
        '\(', '\)', '\[', '\]', '{', '}', '@', ',', ':', '\.', '`',
        '=', ';'
        ]
    
    long_literals = [
        ('<<', 'LSHIFT'),
        ('>>', 'RSHIFT'),
        ('<=', 'LE'),
        ('>=', 'GE'),
        ('==', 'EQ'),
        ('!=', 'NE'),
        ('<>', 'GTLT'),
        (r'\.\.\.', 'ELLIPSIS'),
        ('\*\*', 'POW'),
        ('//', 'FLOOR_DIVIDE'),
    ]
    
    keywords = [
        ('and', 'AND'),
        ('call', 'CALL'),
        ('create', 'CREATE'),
        ('else', 'ELSE'),
        ('if', 'IF'),
        ('is', 'IS'),
        ('for', 'FOR'),
        ('in', 'IN'),
        ('include', 'INCLUDE'),
        ('lambda', 'LAMBDA'),
        ('macro', 'MACRO'),
        ('not', 'NOT'),
        ('or', 'OR'),
        ('search', 'SEARCH'),
        ('set', 'SET'),
    ]
    

    # tokens also includes all the tokens defined in the keywords list above
    tokens = [
        'BLOCK',
        'CONFIGURE',
        'END',
        'EMPTYDICT',
        'EMPTYLIST',
        'EXTEND',
        'KEY',
        'LDBRACE',
        'LISTITEM',
        'RDBRACE',
        'SCALAR',
        'IDENTIFIER',
        'LITERAL',
        'ELIF',
        'SELECT',
        ]
    
    def __init__(self):
        self.indents = {}
        # initial_indent holds the number of spaces prefixing the first real line
        # this is used as the leftmost indent level
        self.initial_indent = None
        self.remaining = []
        self.lineno = 0
        self.lexpos = 0
        self.finished = False
        self.compile()
        
        # these handle state during token generation
        self.multiline = False
        self.template = None
        self.multiline_buffer = []
        self.last_level = 0
        self._generator = self._tokens()
        
    def compile(self):
        self.literals_re = []
        self.keywords_re = []
        self.long_literals_re = []
        for i in self.literals:
            self.literals_re.append(re.compile(i))
        for s, t in self.keywords:
            self.keywords_re.append((re.compile("(%s)($|[^A-Za-z0-9_])" % s), t))
        for s, t in self.long_literals:
            self.long_literals_re.append((re.compile(s), t))
        
    def input(self, text):
        self.remaining.extend(list(text))
        self.done() # is this right? PLY not clear
        
    def remaining_input(self):
        return "".join(self.remaining).strip()
    
    def read_line(self):
        """ Read a line from the input. """
        while self.remaining_input() or not self.finished:
            if not self.remaining:
                raise LexerError("Out of input", line=self.lineno)
            try:
                eol = self.remaining.index("\n")
            except ValueError:
                eol = len(self.remaining)
            line = self.remaining[:eol]
            self.remaining = self.remaining[eol+1:]
            self.lexpos += len(line)
            self.lineno += 1
            line = "".join(line).rstrip(" ")
            # skip comments
            if not line.lstrip().startswith("#"):
                yield line
            
    def parse_indent(self, line):
        spaces = 0
        for char in line:
            if char == " ":
                spaces += 1
            else:
                return spaces, line[spaces:]
        return spaces, ""
    
    def indent_level(self, spaces):
        """ Return the correct indent level for the number of spaces """
        if self.initial_indent == None:
            self.initial_indent = spaces
        if spaces == self.initial_indent:
            # reset indenting
            self.indents = {}
            return 0
        if spaces < self.initial_indent:
            raise LexerError("Dedent below initial indent", line=self.lineno)
        if not self.indents:
            self.indents[spaces] = 1
            return 1
        level = self.indents.get(spaces, None)
        if level is not None:
            return level
        else:
            if spaces < max(self.indents.keys()):
                raise LexerError("Unindent to surprise level", line=self.lineno)
            else:
                self.indents[spaces] = max(self.indents.values())+1
                return self.indents[spaces]
            
    def get_spaces_for_level(self, level):
        insideout = dict((y,x) for (x,y) in self.indents.items())
        return insideout.get(level, 0)
            
    def done(self):
        self.finished = True
            
    def list_key_indent_level(self, line):
        """ This is the case where we have:
        
          - a: b
        
        We need to indent to the 'a' so we can continue to dict.
        """
        spaces, line = self.parse_indent(line)
        assert(line.startswith('-'))
        spaces2, line2 = self.parse_indent(line[1:])
        total_spaces = spaces + 1 + spaces2 # indent the '-' too
        return self.indent_level(total_spaces)

    def emit_multiline(self):
        value = "\n".join(self.multiline_buffer) + "\n"
        for tok in self.parse_value(value):
            yield tok
        self.multiline = False
        self.template = None
        self.multiline_buffer = []
    
    def parse_key(self, key):
        """ Parse a key. Supports the following formats:
          key
          extend key
          configure key
        """
        
        if ' ' not in key:
            return [LexToken('KEY', key)]
        parts = key.split(" ", 2)
        if parts[0] == 'extend':
            return [LexToken('EXTEND'),
                    LexToken('KEY', parts[1])]
        if parts[0] == 'configure':
            return [LexToken('CONFIGURE'),
                    LexToken('KEY', parts[1])]
        raise LexerError("Key contains whitespace", line=self.lineno)
        
    def parse_value(self, value):
        """ Return tokens as required for value """
        if value == '{}':
            yield LexToken('EMPTYDICT')
        elif value == '[]':
            yield LexToken('EMPTYLIST')
        else:
            while value:
                ldbrace = value.find('{{')
                if ldbrace == -1:
                    yield LexToken('SCALAR', value)
                    value = ""
                else:
                    if ldbrace > 0:
                        yield LexToken('SCALAR', value[:ldbrace])
                    yield LexToken('LDBRACE')
                    value = value[ldbrace+2:]
                    rdbrace = value.find('}}')
                    if rdbrace == -1:
                        raise LexerError("Unbalanced {{}}", lineno=self.lineno)
                    for tok in self.parse_command(value[:rdbrace]):
                        yield tok
                    yield LexToken('RDBRACE')
                    value = value[rdbrace+2:]
        
    def match_symbolic_literal(self, line):
        for i in self.literals_re:
            m = i.match(line)
            if m is not None:
                r =  m.group()
                return r
        
    def match_string_literal(self, line):
        """ If there is a literal at the start of this line, then return the
        matching literal. Otherwise return None. """
        
        # shortstring     ::=  "'" shortstringitem* "'" | '"' shortstringitem* '"'
        # longstring      ::=  "'''" longstringitem* "'''"
        #                      | '"""' longstringitem* '"""'
        # shortstringitem ::=  shortstringchar | escapeseq
        # longstringitem  ::=  longstringchar | escapeseq
        # shortstringchar ::=  <any source character except "\" or newline or the quote>
        # longstringchar  ::=  <any source character except "\">
        # escapeseq       ::=  "\" <any ASCII character>
        m = string_literal_re.match(line)
        if m is not None:
            return LexToken('LITERAL', m.group())
        
    def match_integer_literal(self, line):
        """ return integers """
        #longinteger    ::=  integer ("l" | "L")
        #integer        ::=  decimalinteger | octinteger | hexinteger | bininteger
        #decimalinteger ::=  nonzerodigit digit* | "0"
        #octinteger     ::=  "0" ("o" | "O") octdigit+ | "0" octdigit+
        #hexinteger     ::=  "0" ("x" | "X") hexdigit+
        #bininteger     ::=  "0" ("b" | "B") bindigit+
        #nonzerodigit   ::=  "1"..."9"
        #octdigit       ::=  "0"..."7"
        #bindigit       ::=  "0" | "1"
        #hexdigit       ::=  digit | "a"..."f" | "A"..."F"
        m = integer_re.match(line)
        if m is not None:
            ival = eval(m.group())
            return LexToken('LITERAL', ival, orig=m.group())

    def match_floating_point_literal(self, line):
        """ return floating points """
        #floatnumber   ::=  pointfloat | exponentfloat
        #pointfloat    ::=  [intpart] fraction | intpart "."
        #exponentfloat ::=  (intpart | pointfloat) exponent
        #intpart       ::=  digit+
        #fraction      ::=  "." digit+
        #exponent      ::=  ("e" | "E") ["+" | "-"] digit+        
        m = float_re.match(line) 
        if m is not None:
            ival = eval(m.group())
            return LexToken('LITERAL', ival, orig=m.group())

    def match_identifier(self, line):
        """ If there is an identifier at the start of this line, then return the
        matching literal. Otherwise return None. """
        # identifier ::=  (letter|"_") (letter | digit | "_")*
        # letter     ::=  lowercase | uppercase
        # lowercase  ::=  "a"..."z"
        # uppercase  ::=  "A"..."Z"
        # digit      ::=  "0"..."9"
        m = identifier_re.match(line)
        if m is not None:
            return LexToken('IDENTIFIER', m.group())
        
    def match_long_symbolic_literal(self, line):
        """ return literals longer than one character """
        for i, t in self.long_literals_re:
            m = i.match(line)
            if m is not None:
                r =  m.group()
                return LexToken(t, r)
            
    def match_keyword(self, line):
        """ return keywords """
        for i, t in self.keywords_re:
            m = i.match(line)
            if m is not None:
                r =  m.group(1)
                return LexToken(t, r)
        
    def match_command_token(self, line):
        for f in [
            self.match_long_symbolic_literal,
            self.match_symbolic_literal,
            self.match_string_literal,
            self.match_floating_point_literal,
            self.match_integer_literal,
            self.match_keyword,
            self.match_identifier]:
            r = f(line)
            if r is not None:
                return r

    def parse_command(self, line):
        """ A "command" is anything entered in command mode. command mode is generally found by starting a line with a % """
        line = line.strip()
        while line:
            tok = self.match_command_token(line)
            if tok is None:
                raise LexerError("Cannot parse command fragment %r" % line)
            else:
                yield tok
                line = line[len(tok):]
                line = line.lstrip()
        

    def _tokens(self):
        # this function is too long
        # but it is very hard to make shorter
        
        # initial block to wrap them all
        yield LexToken('BLOCK')
        
        for raw_line in self.read_line():
            # handle indents
            spaces, line = self.parse_indent(raw_line)
            
            # blank lines are ignored, unless they are inside a multiline block
            # in which case they are included
            if not line:
                if self.multiline:
                    multiline_buffer.append('\n')
                continue
            
            # find the current indent level
            level = self.indent_level(spaces)
            
            # if the multiline flag is set we are not in standard token processing
            # this is a core state flag
            if self.multiline:
                if not self.multiline_buffer:
                    # first multiline
                    self.last_level = level
                if level == self.last_level:
                    self.multiline_buffer.append(line)
                    continue
                elif level < self.last_level:
                    for tok in self.emit_multiline():
                        yield tok
                    # don't continue, go on to process what is on the line
                elif level > self.last_level:
                    prev_spaces = self.get_spaces_for_level(self.last_level)
                    self.multiline_buffer.append((spaces - prev_spaces) * ' ' + line)
                    continue
                
            # we are now processing non-multiline content
            
            # dedent with END tokens as required to achieve the correct level
            if level < self.last_level:
                for x in range(level, self.last_level):
                    yield LexToken('END')
                    
            # stash the level
            self.last_level = level
            
            # see if this is actually a command line
            if line.startswith('%'):
                yield LexToken('PERCENT')
                line = line[1:]
                for tok in self.parse_command(line):
                    yield tok
            
            # see if the line starts with a key
            elif ':' in line:
                
                # it's a key inside a list value
                if line.startswith('-'):
                    key, value = [x.strip() for x in line.split(":", 1)]
                    key = key[1:].strip()
                    yield LexToken('LISTITEM')
                    yield LexToken('BLOCK')
                    for token in self.parse_key(key):
                        yield token
                    yield LexToken('BLOCK')
                    # push in the level so we end the block correctly
                    self.last_level = self.list_key_indent_level(raw_line)
                else:
                    key, value = [x.strip() for x in line.split(":", 1)]
                    for token in self.parse_key(key):
                        yield token
                    yield LexToken('BLOCK')
                if value:
                    if value == '|':
                        self.multiline = True
                        continue
                    else:
                        for tok in self.parse_value(value):
                            yield tok
                    yield LexToken('END')
            else:
                if level == 0:
                    raise LexerError("No key found on a top level line", line=self.lineno)
                elif line.startswith("- "):
                    yield LexToken('LISTITEM')
                    yield LexToken('BLOCK')
                    for tok in self.parse_value(line[1:].strip()):
                        yield tok
                    yield LexToken('END')
                else:
                    for tok in self.parse_value(line):
                        yield tok
                    
        # emit the multiline if we end the file in multiline mode
        if self.multiline:
            for tok in self.emit_multiline():
                yield tok
            
        # finish with sufficient ends
        for x in range(0, self.last_level):
            yield LexToken('END')
            
        # final enclosing block
        yield LexToken('END')
        
    def token(self):
        try:
            return self._generator.next()
        except StopIteration:
            return None
    
    def __iter__(self):
        for i in self._generator:
            yield i
                
for s, t in Lexer.keywords:
    Lexer.tokens.append(t)
    