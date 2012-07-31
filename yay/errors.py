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


class Error(Exception):

    def get_string(self):
        return self.args[0]


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

    def __init__(self, description, file="<Unknown>", line=0, column=0, snippet=None):
        self.description = description
        self.file = file
        self.line = line
        self.column = column
        self.snippet = snippet

    def get_string(self):
        error = self.description
        error += "\nFile %s, line %d, column %d" % (self.file, self.line, self.column)
        if self.snippet:
            error += "\n%s" % self.snippet
        return error

    def __str__(self):
        return self.get_string()


class SyntaxError(LanguageError):
    pass


class EvaluationError(LanguageError):
    pass


class NoMatching(EvaluationError):
    pass


