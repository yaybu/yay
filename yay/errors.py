# Copyright 2010-2011 Isotoma Limited
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

import sys


def get_exception_context():
    tb = sys.exc_info()[2]
    context = []

    while tb is not None:
        d = tb.tb_frame.f_locals.get('__context__')
        if d:
            context.append("  %s" % d)
        tb = tb.tb_next

    if not context:
        return ""

    return "While:\n" + "\n".join(context)

class Anchor(object):

    """ A very basic anchor that knows only about an error in a file. This is
    only relevant to EOF errors. """

    def __init__(self, parser):
        self.source = parser.source
        self.text = parser.text

    def __str__(self):
        if self.source is None:
            return "standard input"
        else:
            return repr(self.source)

    def long_description(self):
        return ""

class LineAnchor(Anchor):

    def text_line(self):
        """ Find the specified line in the input """
        return self.text.split("\n")[self.lineno-1]

class ColumnAnchor(LineAnchor):

    """ An anchor that is produced when we have an invalid token. We don't
    know so much about this, other than the start location of the token. """

    def __init__(self, parser, token):
        self.source=parser.source
        self.text=parser.text
        self.lineno=token.lineno
        self.lexpos=token.lexpos

    @property
    def column(self):
        last_cr = self.text.rfind('\n',0, self.lexpos)
        if last_cr < 0:
            last_cr = 0
        return (self.lexpos - last_cr) + 1

    def __str__(self):
        if self.source is None:
            filename = "standard input"
        else:
            filename = repr(self.source)
        return "%s at line %d, column %d" % (filename, self.lineno, self.column)

    def long_description(self):
        line = "%4d %s" % (self.lineno, self.text_line())
        pointer = "     %s^" % (" "*(self.column-2),)
        return  "\n".join([line, pointer])

class SpanAnchor(ColumnAnchor):

    """ An anchor produced within a production. This has full information on
    the span of a symbol. """

    def __init__(self, parser, production, index):
        self.source = parser.source
        self.text = parser.text
        self.lineno=production.lineno(index)
        self.lexpos=production.lexpos(index)
        self.linespan=production.linespan(index)
        self.lexspan=production.lexspan(index)

    def text_lines(self):
        """ Find the specified line in the input """
        lines = self.text.split("\n")
        return lines[self.linespan[0]-1:self.linespan[1]-1]

    def long_description(self):
        if self.linespan[0] == self.linespan[1]:
            line = self.text_line()
            pointer = "%s%s" % (" "*(self.column-2), "^"*(self.lexspan[1]-self.lexspan[0]))
            return "\n".join(line, pointer)
        else:
            out = []
            for i, l in enumerate(self.text_lines(), start=self.linespan[0]):
                if l == self.lineno:
                    marker = "*"
                else:
                    marker = " "
                out.append("%-4d %s %s" % (i, marker, l))
                if l == self.lineno:
                    pointer = "%s%s" % (" "*(self.column-1), "^"*(self.lexspan[1]-self.lexspan[0]))
                    out.append(pointer)
            return "\n".join(out)

class Error(Exception):

    def get_string(self):
        return self.args[0]


class NoPredecessor(Error):
    pass

class NotFound(Error):
    """ An asset or referenced file could not be found """
    pass

class NotModified(Error):
    """ An asset or referenced file has not been modified since last time it
    was opened. Use a cached version or request again without etag. """
    pass

class ProgrammingError(Error):
    pass


class LanguageError(Error):

    def __init__(self, description, anchor=None):
        self.description = description
        self.anchor = anchor

    def __str__(self):
        error = self.description
        if self.anchor:
            error += "\nFile %s, line %s, column %s" % (self.anchor.source, self.anchor.lineno, self.anchor.colno)
        #if self.snippet:
        #    error += "\n%s" % self.snippet
        return error
    get_string = __str__


class LexerError(LanguageError):
    pass

class WhitespaceError(LexerError):
    pass

class ParseError(LanguageError):
    pass

class EOFParseError(ParseError):

    def __init__(self, anchor):
        self.anchor = anchor

    def __str__(self):
        return "Unexpected end of file in %s" % self.anchor

class EOLParseError(ParseError):

    def __init__(self, anchor):
        self.anchor = anchor

    def __str__(self):
        short = "Unexpected end of line in %s" % self.anchor
        desc = self.anchor.long_description()
        if desc is not None:
            return "\n".join(short, desc)
        else:
            return short

class UnexpectedSymbolError(ParseError):

    def __init__(self, token, anchor):
        self.token = token
        self.anchor = anchor

    def __str__(self):
        if self.token.value is not None:
            short = "Unexpected %s (%r) in %s" % (self.token.type, self.token.value, self.anchor)
        else:
            short = "Unexpected %s in %s" % (self.token.type, self.anchor)
        desc = self.anchor.long_description()
        if desc is not None:
            return "\n".join([short, desc])
        else:
            return short


class EvaluationError(LanguageError):
    pass

class ZeroDivisionError(EvaluationError):
    pass

class TypeError(LanguageError):
    pass

class CycleError(EvaluationError):
    """
    Raise when a value depends on itself
    """

class ParadoxError(EvaluationError):
    """
    Raised when an include violates causality
    """

class NoMatching(EvaluationError):
    pass

class NoMoreContext(EvaluationError):
    pass

