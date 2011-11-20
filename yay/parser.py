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

class Parser(object):
    def __init__(self, composer):
        self.composer = composer

        if composer and composer.secret:
            self.secret = True
        else:
            self.secret = False

        self.setup_parser()

    def box(self, value):
        b = nodes.Boxed(value)
        b.secret = self.secret
        return b

    def dollar(self, str, words, tokens):
        return self.box("$")

    def boxed_string(self, str, words, tokens):
        return self.box(tokens[0])

    def boxed_int(self, str, words, tokens):
        return self.box(int(tokens[0]))

    def boxed_octal(self, str, words, tokens):
        return self.box(int(tokens[0], 8))

    def concatenation(self, str, words, tokens):
        if len(tokens) == 1:
            return tokens[0]
        c = nodes.Concatenation(*tokens)
        c.secret = self.secret
        return c

    def function_call_action(self, s, w, t):
        return nodes.Function(t[0], t[1])

    def filter_bin_comparison_action(self, s, w, t):
        cls = {
            "=": nodes.Equal,
            "!=": nodes.NotEqual,
            "<": nodes.LessThan,
            "<=": nodes.LessThanEqual,
            ">": nodes.GreaterThan,
            ">=": nodes.GreaterThanEqual,
            }[t[0][1]]
        return cls(t[0][0], t[0][2])

    def filter_expression_action(self, s, w, t):
        node = t[0]
        for i in range(1, len(t)):
            if t[i] == "and":
                node = nodes.And(node, t[i+1])
            elif t[i] == "or":
                node = nodes.Or(node, t[i+1])
            i += 1
        return node

    def handle_expression(self, s, w, t):
        if len(t[0]) == 1:
            return t[0]

        t = t[0]

        node = nodes.Else(t[0])

        for i in range(1, len(t)):
            if i % 2:
                if t[i] != "else":
                    #FIXME: Raise some kind of parasing error
                    pass
            else:
                node.append(t[i])

        return [node]

    def index_access_action(self, s, w, t):
        return nodes.Access(None, t[0])

    def full_expression_action(self, s, w, t):
        node = None
        for token in t:
            if not isinstance(token, nodes.Node):
                node = nodes.Access(node, nodes.Boxed(token))
            else:
                token.container = node
                if node:
                    node.set_parent(token)
                node = token

        return node

    def ugh(self, s, w, t):
        if not t or not t[0]:
            return []
        return self.boxed_string(s, w, t)

    def inline_call(self, s, w, t):
        return nodes.Call(self.composer, t[0])

    def setup_parser(self):
        ELSE = Keyword("else")
        AND = Keyword("and")
        OR = Keyword("or")
        IN = Keyword("in")
        BINOP = oneOf("= != < > <= >=")

        identifier = Word(alphanums+"_") | Keyword("@")
        arithSign = Word("+-",exact=1)

        octNum = Combine(Optional(arithSign) + Suppress("0") + Word(nums)).setParseAction(self.boxed_octal)
        intNum = Combine(Optional(arithSign) + Word(nums)).setParseAction(self.boxed_int)

        expression = Forward()

        macro_call = Word(alphanums+"_.") + Suppress("!")
        macro_call.setParseAction(self.inline_call)

        function_identifier = Word(alphanums+"_")
        function_call = function_identifier + Group(Suppress("(") + Optional(expression + ZeroOrMore(Suppress(",") + expression)) + Suppress(")"))
        function_call.setParseAction(self.function_call_action)

        filterExpression = Forward()

        filter_bin_comparison = Group(expression + BINOP + expression)
        filter_bin_comparison.setParseAction(self.filter_bin_comparison_action)

        filterCondition = (
            filter_bin_comparison |
            ( "(" + filterExpression + ")" )
        )

        filterExpression << filterCondition + ZeroOrMore((AND|OR) + filterExpression)
        filterExpression.setParseAction(self.filter_expression_action)

        full_list_access = Suppress("[") + filterExpression + Suppress("]")
        full_list_access.setParseAction(lambda s, w, t: nodes.Filter(None, t[0]))

        listAccess = Suppress("[") + expression + Suppress("]")
        listAccess.setParseAction(self.index_access_action)


        fullExpression = identifier + ZeroOrMore(
            full_list_access |
            listAccess |
            Suppress(".") + identifier
            )
        fullExpression.setParseAction(self.full_expression_action)

        expression_part = (
            octNum |
            intNum |
            macro_call |
            function_call |
            fullExpression
            )

        expression << Group(expression_part + Optional(ELSE + expression)).setParseAction(self.handle_expression)

        bracketed_expression = Suppress("${").leaveWhitespace() + expression + Suppress("}").leaveWhitespace()

        myrol = restOfLine.copy().setParseAction(self.ugh)

        templated_string = ZeroOrMore(
            Keyword("$$").setParseAction(self.dollar) |
            bracketed_expression |
            SkipTo("${").leaveWhitespace().setParseAction(self.boxed_string)
            ) + myrol
        templated_string.setParseAction(self.concatenation)

        foreachif = Optional(Keyword("if") + filterExpression)

        foreach_statement = identifier + Suppress("in") + expression + Optional(Keyword("chain") | Keyword("nochain") | Keyword("flatten")) + foreachif
        as_statement = expression + Suppress("as") + identifier

        self.templated_string = templated_string
        self.foreach_statement = foreach_statement
        self.as_statement = as_statement
        self.expression = expression

