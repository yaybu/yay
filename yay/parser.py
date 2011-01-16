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

from yay.pyparsing import *

from yay import nodes

class Actions(object):
    def boxed(self, str, words, tokens):
        return nodes.Boxed(tokens[0])
    def boxed_int(self, str, words, tokens):
        return nodes.Boxed(int(tokens[0]))
    def concatenation(self, str, words, tokens):
        if len(tokens) == 1:
            return tokens[0]
        return nodes.Concatenation(*tokens)

actions = Actions()

AND = Keyword("and")
OR = Keyword("or")
IN = Keyword("in")
BINOP = oneOf("= != < > <= >=")

identifier = Word(alphanums+"_")
arithSign = Word("+-",exact=1)
intNum = Combine( Optional(arithSign) + Word( nums ) ).setParseAction(actions.boxed_int)

expression = Forward()

filterExpression = Forward()

def filter_bin_comparison_action(s, w, t):
    cls = {
        "=": nodes.Equal,
        "!=": nodes.NotEqual,
        "<": nodes.LessThan,
        "<=": nodes.LessThanEqual,
        ">": nodes.GreaterThan,
        ">=": nodes.GreaterThanEqual,
        }[t[0][1]]
    return cls(t[0][0], t[0][2])
filter_bin_comparison = Group(expression + BINOP + expression)
filter_bin_comparison.setParseAction(filter_bin_comparison_action)

filterCondition = (
    filter_bin_comparison |
    ( "(" + filterExpression + ")" )
    )

def filter_expression_action(s, w, t):
    node = t[0]
    for i in range(1, len(t)):
        if t[i] == "and":
            node = nodes.And(node, t[i+1])
        elif t[i] == "or":
            node = nodes.Or(node, t[i+1])
        i += 1
    return node
filterExpression << filterCondition + ZeroOrMore((AND|OR) + filterExpression)
filterExpression.setParseAction(filter_expression_action)

def index_access_action(s, w, t):
    return nodes.Access(None, int(t[0]))
indexAccess = intNum.copy()
indexAccess.setParseAction(index_access_action)

listAccess = Suppress("[") + (
    filterExpression |
    indexAccess
    ) + Suppress("]")

def full_expression_action(s, w, t):
    node = None
    for token in t:
        node = nodes.Access(node, token)
    return node
fullExpression = identifier + ZeroOrMore(
    listAccess |
    Suppress(".") + identifier
    )
fullExpression.setParseAction(full_expression_action)

expression << (
    intNum |
    fullExpression
    )


bracketed_expression = Suppress("{") + expression + Suppress("}")

templated_string = ZeroOrMore(SkipTo("{").setParseAction(actions.boxed) + bracketed_expression) + restOfLine.setParseAction(actions.boxed)
templated_string.setParseAction(actions.concatenation)

#print templated_string.parseString("foo bar {foo.ag} foo bar {foo.age} foo baz")[0]
print templated_string.parseString("foo bar baz")[0]
#print repr(expression.parseString("foo.bar[foo.age < 12 and foo.badger > 5][0]")[0])
