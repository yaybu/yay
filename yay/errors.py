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
        return "\n".join(self.long_description_lines())


class LineAnchor(Anchor):

    def text_line(self):
        """ Find the specified line in the input """
        return self.text.split("\n")[self.lineno - 1]


class ColumnAnchor(LineAnchor):

    """ An anchor that is produced when we have an invalid token. We don't
    know so much about this, other than the start location of the token. """

    def __init__(self, parser, token):
        self.source = parser.source
        self.text = parser.text
        self.lineno = token.lineno
        self.lexpos = token.lexpos

    @property
    def column(self):
        last_cr = self.text.rfind('\n', 0, self.lexpos)
        if last_cr < 0:
            last_cr = 0
        return (self.lexpos - last_cr) + 1

    def __str__(self):
        if self.source is None:
            filename = "standard input"
        else:
            filename = repr(self.source)
        return (
            "%s at line %d, column %d" % (filename, self.lineno, self.column)
        )

    def long_description_lines(self):
        line = "%4d %s" % (self.lineno, self.text_line())
        pointer = "     %s^" % (" " * (self.column - 2),)
        return (line, pointer)


class SpanAnchor(ColumnAnchor):

    """ An anchor produced within a production. This has full information on
    the span of a symbol. """

    def __init__(self, parser, production, index):
        self.source = parser.source
        self.text = parser.text
        self.lineno = production.lineno(index)
        self.lexpos = production.lexpos(index)
        self.linespan = production.linespan(index)
        self.lexspan = production.lexspan(index)

    def text_lines(self):
        """ Find the specified line in the input """
        lines = self.text.split("\n")
        return lines[self.linespan[0] - 1:self.linespan[1] - 1]

    def long_description_lines(self):
        if self.linespan[0] == self.linespan[1]:
            line = self.text_line()
            pointer = "%s%s" % (
                " " * (self.column - 1), "^" * (self.lexspan[1] - self.lexspan[0] + 1))
            return (line, pointer)
        else:
            out = []
            for i, l in enumerate(self.text_lines(), start=self.linespan[0]):
                if l == self.lineno:
                    marker = "*"
                else:
                    marker = " "
                out.append("%-4d %s %s" % (i, marker, l))
                if l == self.lineno:
                    pointer = "%s%s" % (
                        " " * (self.column - 1), "^" * (self.lexspan[1] - self.lexspan[0]))
                    out.append(pointer)
            return out


class AnchorCollection(object):

    def __init__(self, collection=None):
        self.collection = collection or []

    def long_description(self):
        descriptions = []
        for anchor in self.collection:
            descriptions.append("  " + str(anchor))
            for line in anchor.long_description_lines():
                descriptions.append("    " + line)
        return '\n'.join(descriptions)


def merge_anchors(existing, incoming):
    if not existing:
        existing = AnchorCollection()
    if not isinstance(existing, AnchorCollection):
        existing = AnchorCollection([existing])
    if incoming:
        existing.collection.insert(0, incoming)
    return existing


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
        error = [self.description]
        if self.anchor:
            error.append(self.anchor.long_description())
        # else:
        #    error.append("No anchor is available for this error - please file a bug!")
        return "\n".join(error)
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
        self.description = "Unexpected end of line in %s" % self.anchor

    def __str__(self):
        desc = self.anchor.long_description()
        if desc is not None:
            return "\n".join([self.description, desc])
        else:
            return self.description


class UnexpectedSymbolError(ParseError):

    def __init__(self, token, anchor):
        self.token = token
        self.anchor = anchor

    def __str__(self):
        if self.token.value is not None and self.token.value.lower() != self.token.type.lower():
            short = "Unexpected %s (%r) in %s" % (
                self.token.type.lower(), self.token.value, self.anchor)
        else:
            short = "Unexpected '%s' in %s" % (
                self.token.type.lower(), self.anchor)
        desc = self.anchor.long_description()
        if desc is not None:
            return "\n".join([short, desc])
        else:
            return short
    get_string = __str__


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
