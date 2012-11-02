
class LexerError(Exception):
    pass

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

class VALUE(Token):
    pass

class ENDBLOCK(Token):
    def __repr__(self):
        return "<ENDBLOCK>"

class LISTVALUE(Token):
    pass

class Lexer(object):
    
    def __init__(self):
        self.indents = {}
        self.remaining = []
        self.finished = False
        
    def input(self, text):
        self.remaining.extend(list(text))
        
    def read_line(self):
        """ Read a line from the input. """
        while self.remaining or not self.finished:
            if not self.remaining:
                raise LexerError("Out of input")
            try:
                eol = self.remaining.index("\n")
            except ValueError:
                raise LexerError("Out of lines")
            line = self.remaining[:eol]
            self.remaining = self.remaining[eol+1:]
            yield "".join(line).rstrip(" ")
            
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
        if spaces == 0:
            # reset indenting
            self.indents = {}
            return 0
        if not self.indents:
            self.indents[spaces] = 1
            return 1
        level = self.indents.get(spaces, None)
        if level is not None:
            return level
        else:
            if spaces < max(self.indents.keys()):
                raise LexerError("Unindent to surprise level")
            else:
                self.indents[spaces] = max(self.indents.values())+1
                return self.indents[spaces]
            
    def done(self):
        self.finished = True
            
    def tokens(self):
        last_level = 0
        for line in self.read_line():
            # handle indents
            spaces, line = self.parse_indent(line)
            if not line:
                # we ignore blank lines completely
                continue
            level = self.indent_level(spaces)
            if level < last_level:
                for x in range(level, last_level):
                    yield ENDBLOCK()
            last_level = level
            # see if the line starts with a key
            if ':' in line:
                key, value = line.split(":", 1)
                yield KEY(key)
                if value:
                    yield VALUE(value.lstrip(" "))
                    yield ENDBLOCK()
            else:
                if level == 0:
                    raise LexerError("No key found on a top level line")
                elif line.startswith("- "):
                    yield LISTVALUE(line[2:])
                else:
                    yield VALUE(line)
        for x in range(0, last_level):
            yield ENDBLOCK()
                
            