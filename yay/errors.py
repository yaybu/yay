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

class Error(Exception):

    def get_string(self):
        return self.args[0]


class LanguageError(Error):

    def __init__(self, description, file, line, column, snippet=None):
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


class SyntaxError(LanguageError):
    pass


class EvaluationError(LanguageError):
    pass



