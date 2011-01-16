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

from yay.pyparsing import Forward, Group, Keyword, Optional, Word, \
    ZeroOrMore, oneOf, alphas, nums, alphanums, Combine, Suppress

from yay import nodes

AND = Keyword("and")
OR = Keyword("or")
IN = Keyword("in")
BINOP = oneOf("= != < > <= >=")

identifier = Word(alphanums+"_")
arithSign = Word("+-",exact=1)
intNum = Combine( Optional(arithSign) + Word( nums ) ).setParseAction(lambda s, w, t: nodes.Boxed(int(t[0])))

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

print repr(fullExpression.parseString("foo.bar[foo.age < 12 and foo.badger > 5][0]")[0])
