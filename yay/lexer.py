
class LexerError(Exception):
    
    def __init__(self, message, lineno=None, line=None):
        self.message = message
        self.lineno = lineno
        self.line = line

class Token(object):
    
    def __init__(self, value=None):
        self.value = value
        
    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.value)
    
    def __cmp__(self, x):
        if self.__class__.__name__ == x.__class__.__name__ and self.value == x.value:
            return 0
        return 1

class KEY(Token):
    pass

class SCALAR(Token):
    pass

class BLOCK(Token):
    def __repr__(self):
        return "<BLOCK>"
    
class END(Token):
    def __repr__(self):
        return "<END>"

class LISTITEM(Token):
    def __repr__(self):
        return "<LISTITEM>"

class EMPTYDICT(Token):
    pass

class EMPTYLIST(Token):
    pass

class Lexer(object):
    
    def __init__(self):
        self.indents = {}
        # initial_indent holds the number of spaces prefixing the first real line
        # this is used as the leftmost indent level
        self.initial_indent = None
        self.remaining = []
        self.lineno = 0
        self.finished = False
        
    def input(self, text):
        self.remaining.extend(list(text))
        
    def remaining_input(self):
        return "".join(self.remaining).strip()
    
    def read_line(self):
        """ Read a line from the input. """
        while self.remaining_input() or not self.finished:
            if not self.remaining:
                raise LexerError("Out of input")
            try:
                eol = self.remaining.index("\n")
            except ValueError:
                eol = len(self.remaining)
            line = self.remaining[:eol]
            self.remaining = self.remaining[eol+1:]
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
            raise LexerError("Dedent below initial indent", self.lineno)
        if not self.indents:
            self.indents[spaces] = 1
            return 1
        level = self.indents.get(spaces, None)
        if level is not None:
            return level
        else:
            if spaces < max(self.indents.keys()):
                raise LexerError("Unindent to surprise level", self.lineno)
            else:
                self.indents[spaces] = max(self.indents.values())+1
                return self.indents[spaces]
            
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
        
    def tokens(self):
        last_level = 0
        for raw_line in self.read_line():
            # handle indents
            spaces, line = self.parse_indent(raw_line)
            if not line:
                # we ignore blank lines completely
                continue
            level = self.indent_level(spaces)
            if level < last_level:
                for x in range(level, last_level):
                    yield END()
            last_level = level
            # see if the line starts with a key
            if ':' in line:
                if line.startswith('-'):
                    key, value = [x.strip() for x in line.split(":", 1)]
                    key = key[1:].strip()
                    yield LISTITEM()
                    yield BLOCK()
                    yield KEY(key)
                    yield BLOCK()
                    # push in the level so we end the block correctly
                    last_level = self.list_key_indent_level(raw_line)
                else:
                    key, value = [x.strip() for x in line.split(":", 1)]
                    yield KEY(key)
                    yield BLOCK()
                if value:
                    if value == '{}':
                        yield EMPTYDICT()
                    elif value == '[]':
                        yield EMPTYLIST()
                    else:
                        yield SCALAR(value)
                    yield END()
            else:
                if level == 0:
                    raise LexerError("No key found on a top level line", lineno, line)
                elif line.startswith("- "):
                    yield LISTITEM()
                    yield BLOCK()
                    yield SCALAR(line[2:])
                    yield END()
                else:
                    yield SCALAR(line)
        for x in range(0, last_level):
            yield END()
                
            