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
    def boxed_octal(self, str, words, tokens):
        return nodes.Boxed(int(tokens[0], 8))
    def concatenation(self, str, words, tokens):
        if len(tokens) == 1:
            return tokens[0]
        return nodes.Concatenation(*tokens)

actions = Actions()

AND = Keyword("and")
OR = Keyword("or")
IN = Keyword("in")
BINOP = oneOf("= != < > <= >=")

identifier = Word(alphanums+"_") | Keyword("@")
arithSign = Word("+-",exact=1)

octNum = Combine(Optional(arithSign) + Suppress("0") + Word(nums)).setParseAction(actions.boxed_octal)
intNum = Combine(Optional(arithSign) + Word(nums)).setParseAction(actions.boxed_int)

expression = Forward()

def function_call_action(s, w, t):
    return nodes.Function(t[0], t[1])
function_identifier = Word(alphanums+"_")
function_call = function_identifier + Group(Suppress("(") + Optional(expression + ZeroOrMore(Suppress(",") + expression)) + Suppress(")"))
function_call.setParseAction(function_call_action)

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


full_list_access = Suppress("[") + filterExpression + Suppress("]")
full_list_access.setParseAction(lambda s, w, t: nodes.Filter(None, t[0]))


def index_access_action(s, w, t):
    return nodes.Access(None, t[0])
listAccess = Suppress("[") + intNum + Suppress("]")
listAccess.setParseAction(index_access_action)


def full_expression_action(s, w, t):
    node = None
    for token in t:
        if not isinstance(token, nodes.Node):
            node = nodes.Access(node, token)
        else:
            token.container = node
            node = token
    return node

fullExpression = identifier + ZeroOrMore(
    full_list_access |
    listAccess |
    Suppress(".") + identifier
    )
fullExpression.setParseAction(full_expression_action)

expression << (
    octNum |
    intNum |
    function_call |
    fullExpression
    )


bracketed_expression = Suppress("${") + expression + Suppress("}")


def ugh(s, w, t):
    if not t or not t[0]:
        return []
    return actions.boxed(s, w, t)
myrol = restOfLine.copy().setParseAction(ugh)

templated_string = ZeroOrMore(
    bracketed_expression |
    SkipTo("${").leaveWhitespace().setParseAction(actions.boxed)
    ) + myrol
templated_string.setParseAction(actions.concatenation)

as_statement = identifier + Suppress("in") + expression

#print as_statement.parseString("foolist[foo.age < bar.maxage] as person")
#print templated_string.parseString("foo bar {foo.ag} foo bar {foo.age} foo baz")[0]
#print templated_string.parseString("{foo.bar.baz}")[0]
#print repr(expression.parseString("foo.bar[foo.age < 12 and foo.badger > 5][0]")[0])
#print fullExpression.parseString("foo.bar")
