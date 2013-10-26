# Copyright 2012 Isotoma Limited
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

import os
from ply import yacc

# Support python 3
OldYaccProduction = yacc.YaccProduction


class YaccProduction(OldYaccProduction):

    def __getitem__(self, n):
        if isinstance(n, slice):  # pragma: no cover
            return [s.value for s in self.slice[n]]
        return OldYaccProduction.__getitem__(self, n)
yacc.YaccProduction = YaccProduction

# don't bleat about unused terminals
# be nice to only turn this on if we're in debug mode
yacc.Grammar.unused_terminals = lambda self: ()

from .lexer import Lexer, ExpressionLexer
from . import ast
from .errors import (Anchor, ColumnAnchor, SpanAnchor,
                     EOLParseError, EOFParseError,
                     UnexpectedSymbolError)

import warnings

expressions = {
    "==": ast.Equal,
    "!=": ast.NotEqual,
    "<": ast.LessThan,
    ">": ast.GreaterThan,
    "<=": ast.LessThanEqual,
    ">=": ast.GreaterThanEqual,
    "+": ast.Add,
    "-": ast.Subtract,
    "*": ast.Multiply,
    "/": ast.Divide,
    "//": ast.FloorDivide,
    "%": ast.Mod,
    "<<": ast.Lshift,
    ">>": ast.Rshift,
    "^": ast.Xor,
    "or": ast.Or,
    "|": ast.BitwiseOr,
    "and": ast.And,
    "&": ast.BitwiseAnd,
    "not in": ast.NotIn,
}


class BaseParser(object):

    start = 'root'
    Lexer = Lexer

    def __init__(self, lexer=None):
        self.lexer = lexer or self.Lexer
        self.tokens = self.lexer.tokens

        outputdir = os.path.dirname(__file__)
        parsetab = os.path.join(outputdir, "parsetab.py")
        write_tables = 0
        if os.path.exists(parsetab):
            if os.access(parsetab, os.W_OK):
                write_tables = 1
        elif os.access(outputdir, os.W_OK):
            write_tables = 1

        self.parser = yacc.yacc(module=self,
                                debug=0,
                                tabmodule='yay.parsetab',
                                outputdir=os.path.dirname(__file__),
                                write_tables=write_tables,
                                )

    def parse(self, value, source="<unknown>", tracking=True, debug=False):
        self.errors = 0
        self.source = source
        self.text = value
        rv = self.parser.parse(value,
                               lexer=self.lexer(source=source),
                               tracking=tracking,
                               debug=debug
                               )
        if self.errors > 0:
            raise SyntaxError
        return rv

    def anchor(self, p, i):
        """ Set the position of p[0] from symbol i """
        p[0].anchor = SpanAnchor(self, p, i)

    # EXPRESSIONS
    # http://docs.python.org/2/reference/expressions.html

    # Atoms are the most basic elements of expressions. The simplest atoms
    # are identifiers or literals. Forms enclosed in reverse quotes or in
    # parentheses, brackets or braces are also categorized syntactically as
    # atoms.

    def p_atom_identifier(self, p):
        '''
        atom : identifier
        '''
        p[0] = p[1]
        self.anchor(p, 1)

    def p_atom_literal(self, p):
        '''
        atom : STRING
             | INTEGER
             | FLOAT
        '''
        p[0] = ast.Literal(p[1])
        self.anchor(p, 1)

    def p_atom_enclosure(self, p):
        '''
        atom : enclosure
        '''
        p[0] = p[1]

    def p_enclosure(self, p):
        '''
        enclosure : parenth_form
                  | list_display
                  | generator_expression
                  | dict_display
                  | set_display
                  | string_conversion
        '''
        p[0] = p[1]

    def p_parent_form(self, p):
        '''
        parenth_form : "(" ")"
                     | "(" expression_list ")"
        '''
        # A parenthesized form is an optional expression list enclosed in
        # parentheses
        #
        # A parenthesized expression list yields whatever that expression list
        # yields: if the list contains at least one comma, it yields a tuple;
        # otherwise, it yields the single expression that makes up the expression
        # list.
        #
        # An empty pair of parentheses yields an empty tuple object. Since tuples
        # are immutable, the rules for literals apply (i.e., two occurrences of
        # the empty tuple may or may not yield the same object).
        #
        # Note that tuples are not formed by the parentheses, but rather by use
        # of the comma operator. The exception is the empty tuple, for which
        # parentheses are required - allowing unparenthesized "nothing" in
        # expressions would cause ambiguities and allow common typos to pass
        # uncaught.

        if len(p) == 3:
            p[0] = ast.ParentForm()
        else:
            p[0] = ast.ParentForm(p[2])
        self.anchor(p, 1)

    def p_list_display(self, p):
        '''
        list_display : "[" "]"
                     | "[" expression_list "]"
                     | "[" list_comprehension "]"
        '''
        # A list display is a possibly empty series of expressions enclosed in
        # square brackets.
        #
        # A list display yields a new list object. Its contents are specified by
        # providing either a list of expressions or a list comprehension. When a
        # comma-separated list of expressions is supplied, its elements are
        # evaluated from left to right and placed into the list object in that
        # order. When a list comprehension is supplied, it consists of a single
        # expression followed by at least one for clause and zero or more for or
        # if clauses. In this case, the elements of the new list are those that
        # would be produced by considering each of the for or if clauses a block,
        # nesting from left to right, and evaluating the expression to produce a
        # list element each time the innermost block is reached.
        if len(p) == 3:
            p[0] = ast.ListDisplay()
        else:
            p[0] = ast.ListDisplay(p[2])
        self.anchor(p, 1)

    def p_list_comprehension(self, p):
        '''
        list_comprehension : expression list_for
        '''
        p[0] = ast.ListComprehension(p[1], p[2])
        self.anchor(p, 1)

    def p_list_for(self, p):
        '''
        list_for : FOR target_list IN old_expression_list
                 | FOR target_list IN old_expression_list list_iter
        '''
        if len(p) == 5:
            p[0] = ast.ListFor(p[2], p[4])
        else:
            p[0] = ast.ListFor(p[2], p[4], p[5])
        self.anchor(p, 1)

    def p_old_expression_list(self, p):
        '''
        old_expression_list : old_expression
                            | old_expression_list "," old_expression
                            | old_expression_list ","
        '''
        # exactly the same semantics
        self.p_expression_list(p)

    def p_old_expression(self, p):
        '''
        old_expression : or_test
                       | old_lambda_form
        '''
        p[0] = p[1]

    def p_list_iter(self, p):
        '''
        list_iter : list_for
                  | list_if
        '''
        p[0] = p[1]

    def p_list_if(self, p):
        '''
        list_if : IF old_expression
                | IF old_expression list_iter
        '''
        if len(p) == 3:
            p[0] = ast.ListIf(p[2])
        else:
            p[0] = ast.ListIf(p[2], p[3])

    def p_comprehension(self, p):
        '''
        comprehension : expression comp_for
        '''
        p[0] = ast.Comprehension(p[1], p[2])

    def p_comp_for(self, p):
        '''
        comp_for : FOR target_list IN or_test
                 | FOR target_list IN or_test comp_iter
        '''
        if len(p) == 5:
            p[0] = ast.CompFor(p[2], p[4])
        else:
            p[0] = ast.CompFor(p[2], p[4], p[5])

    def p_comp_iter(self, p):
        '''
        comp_iter : comp_for
                  | comp_if
        '''
        p[0] = p[1]

    def p_comp_if(self, p):
        '''
        comp_if : IF expression
                | IF expression comp_iter
        '''

        # expression is actually "expression_nocond" in the grammar
        # i do not know what this means
        # http://docs.python.org/2/reference/expressions.html#displays-for-sets-and-dictionaries
        if len(p) == 3:
            p[0] = ast.CompIf(p[2])
        else:
            p[0] = ast.CompIf(p[2], p[3])
        self.anchor(p, 1)

    def p_generator_expression(self, p):
        '''
        generator_expression : "(" expression comp_for ")"
        '''
        p[0] = ast.GeneratorExpression(p[2], p[3])
        self.anchor(p, 1)

    def p_dict_display(self, p):
        '''
        dict_display : "{" "}"
                     | "{" key_datum_list "}"
                     | "{" dict_comprehension "}"
        '''
        if len(p) == 3:
            p[0] = ast.DictDisplay()
        else:
            p[0] = ast.DictDisplay(p[2])
        self.anchor(p, 1)

    def p_key_datum_list(self, p):
        '''
        key_datum_list : key_datum
                       | key_datum_list "," key_datum
        '''
        if len(p) == 2:
            p[0] = ast.KeyDatumList(p[1])
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_key_datum(self, p):
        '''
        key_datum : expression ":" expression
        '''
        p[0] = ast.KeyDatum(p[1], p[3])
        self.anchor(p, 2)

    def p_dict_comprehension(self, p):
        '''
        dict_comprehension : expression ":" expression comp_for
        '''
        p[0] = ast.DictComprehension(p[1], p[3], p[4])
        self.anchor(p, 1)

    def p_set_display(self, p):
        '''
        set_display : "{" expression_list "}"
                    | "{" comprehension "}"
        '''
        p[0] = ast.SetDisplay(p[2])
        self.anchor(p, 1)

    def p_string_conversion(self, p):
        '''
        string_conversion : "`" expression_list "`"
        '''
        p[0] = ast.StringConversion(p[2])
        self.anchor(p, 1)

    def p_primary(self, p):
        '''
        primary : atom
                | attributeref
                | subscription
                | slice
                | call
        '''
        p[0] = p[1]

    def p_attributeref(self, p):
        '''
        attributeref : primary "." IDENTIFIER
        '''
        p[0] = ast.AttributeRef(p[1], p[3])
        p[0].anchor = p[1].anchor

    def p_subscription(self, p):
        '''
        subscription : primary "[" expression_list "]"
        '''
        p[0] = ast.Subscription(p[1], p[3])
        p[0].anchor = p[1].anchor

    def p_slice(self, p):
        '''
        slice : primary "[" proper_slice "]"
        '''
        p[0] = ast.SimpleSlicing(p[1], p[3])
        self.anchor(p, 2)

    def p_proper_slice(self, p):
        '''
        proper_slice : short_slice
                     | long_slice
        '''
        p[0] = p[1]

    def p_short_slice_lower_only(self, p):
        '''
        short_slice : lower_bound ":"
        '''
        p[0] = ast.Slice(p[1], None)
        p[0].anchor = p[1].anchor

    def p_short_slice_upper_only(self, p):
        '''
        short_slice : ":" upper_bound
        '''
        p[0] = ast.Slice(None, p[2])
        self.anchor(p, 1)

    def p_short_slice_both(self, p):
        '''
        short_slice : lower_bound ":" upper_bound
        '''
        p[0] = ast.Slice(p[1], p[3])
        p[0].anchor = p[1].anchor

    def p_long_slice(self, p):
        '''
        long_slice : short_slice ":"
                   | short_slice ":" stride
        '''
        p[0] = p[1]
        if len(p) == 4:
            p[0].stride = p[3]

    def p_lower_bound(self, p):
        '''
        lower_bound : expression
        '''
        p[0] = p[1]

    def p_upper_bound(self, p):
        '''
        upper_bound : expression
        '''
        p[0] = p[1]

    def p_stride(self, p):
        '''
        stride : expression
        '''
        p[0] = p[1]

    def p_call(self, p):
        '''
        call : primary "(" ")"
             | primary "(" argument_list ")"
        '''
        # some other stuff in here for genexpr_for that i don't grok
        if len(p) == 4:
            p[0] = ast.Call(p[1])
        else:
            p[0] = ast.Call(p[1], p[3].args, p[3].kwargs)
        p[0].anchor = p[1].anchor

    def p_argument_list_with_positional(self, p):
        '''
        argument_list : positional_arguments
                      | positional_arguments ","
                      | positional_arguments "," keyword_arguments
                      | positional_arguments "," keyword_arguments ","
        '''
        if len(p) in (2, 3):
            p[0] = ast.ArgumentList(p[1].args)
        else:
            p[0] = ast.ArgumentList(p[1].args, p[3].kwargs)
        p[0].anchor = p[1].anchor

    def p_argument_list_no_positional(self, p):
        '''
        argument_list : keyword_arguments
                      | keyword_arguments ","
        '''
        p[0] = ast.ArgumentList(None, p[1])
        p[0].anchor = p[1].anchor

    def p_positional_arguments(self, p):
        '''
        positional_arguments : expression
                             | positional_arguments "," expression
        '''
        if len(p) == 2:
            p[0] = ast.PositionalArguments(p[1])
            p[0].anchor = p[1].anchor
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_keyword_arguments(self, p):
        '''
        keyword_arguments : kwarg
                          | keyword_arguments "," kwarg
        '''
        if len(p) == 2:
            p[0] = ast.KeywordArguments(p[1])
            p[0].anchor = p[1].anchor
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_kwarg(self, p):
        '''
        kwarg : identifier "=" expression
        '''
        p[0] = ast.Kwarg(p[1], p[3])
        self.anchor(p, 1)

    def p_power(self, p):
        '''
        power : primary
              | primary POW u_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ast.Power(p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_u_expr(self, p):
        '''
        u_expr : power
               | "-" u_expr
               | "+" u_expr
               | "~" u_expr
        '''
        # The unary - (minus) operator yields the negation of its numeric
        # argument.
        #
        # The unary + (plus) operator yields its numeric argument unchanged.
        #
        # The unary ~ (invert) operator yields the bitwise inversion of its plain
        # or long integer argument. The bitwise inversion of x is defined as
        # -(x+1). It only applies to integral numbers.
        #
        # In all three cases, if the argument does not have the proper type, a
        # TypeError exception is raised.
        if len(p) == 2:
            p[0] = p[1]
        else:
            if p[1] == '-':
                p[0] = ast.UnaryMinus(p[2])
                self.anchor(p, 1)
            elif p[1] == '+':
                p[0] = p[2]
            elif p[1] == '~':
                p[0] = ast.Invert(p[2])
                self.anchor(p, 1)

    def p_m_expr(self, p):
        '''
        m_expr : u_expr
               | m_expr "*" u_expr
               | m_expr FLOOR_DIVIDE u_expr
               | m_expr "/" u_expr
               | m_expr "%" u_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_a_expr(self, p):
        '''
        a_expr : m_expr
               | a_expr "+" m_expr
               | a_expr "-" m_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_shift_expr(self, p):
        '''
        shift_expr : a_expr
                   | shift_expr LSHIFT a_expr
                   | shift_expr RSHIFT a_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_and_expr(self, p):
        '''
        and_expr : shift_expr
                 | and_expr "&" shift_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_xor_expr(self, p):
        '''
        xor_expr : and_expr
                 | xor_expr "^" and_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_or_expr(self, p):
        '''
        or_expr : xor_expr
                | or_expr "|" xor_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_comparison(self, p):
        '''
        comparison : or_expr
                   | or_expr comp_operator or_expr
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_comp_operator(self, p):
        '''
        comp_operator : "<"
                      | ">"
                      | EQ
                      | GE
                      | LE
                      | GTLT
                      | NE
                      | IS
                      | IS NOT
                      | NOT
                      | NOT IN
        '''
        p[0] = " ".join(p[1:])

    def p_or_test(self, p):
        '''
        or_test : and_test
                | or_test OR and_test
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_and_test(self, p):
        '''
        and_test : not_test
                 | and_test AND not_test
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = expressions[p[2]](p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_not_test(self, p):
        '''
        not_test : comparison
                 | NOT not_test
        '''
        if len(p) == 2:
            p[0] = p[1]
            p[0].anchor = p[1].anchor
        else:
            p[0] = ast.Not(p[2])
            self.anchor(p, 1)

    def p_conditional_expression(self, p):
        '''
        conditional_expression : or_test
                               | expression IF or_test ELSE expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ast.ConditionalExpression(p[3], p[1], p[5])
            p[0].anchor = p[1].anchor

    def p_else(self, p):
        '''
        else_test : expression ELSE expression
        '''
        p[0] = ast.Else(p[1], p[3])
        self.anchor(p, 1)

    def p_expression(self, p):
        '''
        expression : conditional_expression
                   | else_test
                   | lambda_form
        '''
        p[0] = p[1]

    def p_lambda_form(self, p):
        '''
        lambda_form : LAMBDA ":" expression
                    | LAMBDA parameter_list ":" expression
        '''
        if len(p) == 4:
            p[0] = ast.LambdaForm(expression=p[3])
        else:
            p[0] = ast.LambdaForm(params=p[2], expression=p[4])

    def p_old_lambda_form(self, p):
        '''
        old_lambda_form : LAMBDA ":" expression
                        | LAMBDA parameter_list ":" old_expression
        '''
        self.p_lambda_form(p)

    def p_expression_list(self, p):
        '''
        expression_list : expression
                        | expression_list "," expression
                        | expression_list ","
        '''
        # we only create actual expression list objects if we need them
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = p[1]
        else:
            if isinstance(p[1], ast.ExpressionList):
                p[0] = p[1]
                p[0].append(p[3])
            else:
                p[0] = ast.ExpressionList(p[1], p[3])
                p[0].anchor = p[1].anchor

    # SIMPLE STATEMENTS
    # http://docs.python.org/2/reference/simple_stmts.html

    def p_target_list(self, p):
        '''
        target_list : target
                    | target_list "," target
                    | target_list ","
        '''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = p[1]
        else:
            if isinstance(p[1], ast.TargetList):
                p[0] = p[1]
                p[0].append(p[3])
            else:
                p[0] = ast.TargetList(p[1], p[3])
                p[0].anchor = p[1].anchor

    def p_identifier(self, p):
        '''
        identifier : IDENTIFIER
        '''
        p[0] = ast.Identifier(p[1])
        self.anchor(p, 1)

    def p_target(self, p):
        '''
        target : identifier
               | attributeref
               | subscription
               | slice
        '''
        p[0] = p[1]

    # COMPOUND STATEMENTS
    # http://docs.python.org/2/reference/compound_stmts.html

    def p_parameter_list(self, p):
        '''
        parameter_list : defparameter
                       | parameter_list "," defparameter
                       | parameter_list ","
        '''
        if len(p) == 2:
            p[0] = ast.ParameterList(p[1])
            p[0].anchor = p[1].anchor
        elif len(p) == 3:
            p[0] = p[1]
        else:
            p[0] = p[1]
            p[0].append(p[3])

    def p_defparameter(self, p):
        '''
        defparameter : parameter
                     | parameter "=" expression
        '''
        if len(p) == 2:
            p[0] = ast.DefParameter(p[1])
            p[0].anchor = p[1].anchor
        else:
            p[0] = ast.DefParameter(p[1], p[3])
            p[0].anchor = p[1].anchor

    def p_parameter(self, p):
        '''
        parameter : identifier
                  | "(" sublist ")"
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]

    def p_sublist(self, p):
        '''
        sublist : parameter
                | sublist "," parameter
                | sublist ","
        '''
        if len(p) == 2:
            p[0] = ast.Sublist(p[1])
            p[0].anchor = p[1].anchor
        elif len(p) == 3:
            p[0] = p[1]
        else:
            p[0] = p[1]
            p[0].append(p[3])

    # yay \o/

    def p_directive(self, p):
        '''
        directive : include_directive
                  | search_directive
                  | new_directive
                  | prototype_directive
                  | for_directive
                  | set_directive
                  | if_directive
                  | select_directive
                  | macro_directive
                  | call_directive
                  | err_else
        '''
        p[0] = p[1]

    def p_err_else(self, p):
        '''
        err_else : ELSE ":" NEWLINE INDENT stanzas DEDENT
        '''
        self.errors += 1
        warnings.warn("Unmatched else at line %d" % p.lineno(1), SyntaxWarning)

    def p_directives(self, p):
        '''
        directives : directive directive
        '''
        p[0] = ast.Directives(p[1], p[2])
        p[0].anchor = p[1].anchor

    def p_directives_merge(self, p):
        '''
        directives : directives directive
        '''
        p[0] = p[1]
        p[0].append(p[2])

    def p_include_directive(self, p):
        '''
        include_directive : INCLUDE expression_list NEWLINE
        '''
        p[0] = ast.Include(p[2])
        self.anchor(p, 1)

    def p_search_directive(self, p):
        '''
        search_directive : SEARCH expression_list NEWLINE
        '''
        p[0] = ast.Search(p[2])
        self.anchor(p, 1)

    def p_macro_directive(self, p):
        '''
        macro_directive : MACRO target_list ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.Ephemeral(p[2], ast.Macro(p[6]))
        self.anchor(p, 1)
        p[0].inner.anchor = p[0].anchor

    def p_call_directive(self, p):
        '''
        call_directive : CALL target_list ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.CallDirective(p[2], p[6])
        self.anchor(p, 1)

    def p_for_directive(self, p):
        '''
        for_directive : FOR target_list IN expression_list ":" NEWLINE INDENT stanzas DEDENT
                      | FOR target_list IN or_test IF expression ":" NEWLINE INDENT stanzas DEDENT
        '''
        if len(p) == 10:
            p[0] = ast.For(p[2], p[4], p[8])
        else:
            p[0] = ast.For(p[2], p[4], p[10], p[6])
        self.anchor(p, 1)

    def p_set_directive(self, p):
        '''
        set_directive : SET target_list "=" expression_list NEWLINE
        '''
        p[0] = ast.Set(p[2], p[4])
        self.anchor(p, 1)

    def p_if_directive_plain(self, p):
        '''
        if_directive : IF expression_list ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.If(p[2], p[6])
        self.anchor(p, 1)

    def p_if_directive_else(self, p):
        '''
        if_directive : IF expression_list ":" NEWLINE INDENT stanzas DEDENT ELSE ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.If(p[2], p[6], p[12])
        self.anchor(p, 1)

    def p_if_directive_elif(self, p):
        '''
        if_directive : IF expression_list ":" NEWLINE INDENT stanzas DEDENT elif_list
        '''
        p[0] = ast.If(p[2], p[6], p[8])
        self.anchor(p, 1)

    def p_if_directive_else_elif(self, p):
        '''
        if_directive : IF expression_list ":" NEWLINE INDENT stanzas DEDENT elif_list ELSE ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.If(p[2], p[6], p[8])
        p[0].add_else(p[13])
        self.anchor(p, 1)

    def p_elif_list(self, p):
        '''
        elif_list : elif
                  | elif_list elif
        '''
        p[0] = p[1]
        if len(p) != 2:
            p[0].add_elif(p[2])

    def p_elif(self, p):
        '''
        elif : ELIF expression_list ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.If(p[2], p[6])
        self.anchor(p, 1)

    def p_new_as_directive(self, p):
        '''
        new_directive : NEW expression_list AS identifier ":" NEWLINE INDENT stanzas DEDENT
        '''
        new = ast.New(p[2], p[8])
        p[0] = ast.YayDict([(p[4].identifier, new)])
        self.anchor(p, 1)
        new.anchor = p[0].anchor

    def p_new_directive(self, p):
        '''
        new_directive : NEW expression_list ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.New(p[2], p[6])
        self.anchor(p, 1)

    def p_prototype_directive(self, p):
        '''
        prototype_directive : PROTOTYPE expression_list ":" NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.Ephemeral(p[2], ast.Prototype(p[6]))
        self.anchor(p, 1)

    def p_select_directive(self, p):
        '''
        select_directive : SELECT expression_list ":" NEWLINE INDENT case_list DEDENT
        '''
        p[0] = ast.Select(p[2], p[6])
        self.anchor(p, 1)

    def p_case_list(self, p):
        '''
        case_list : case_block
                  | case_list case_block
        '''
        if len(p) == 2:
            p[0] = ast.CaseList(p[1])
            p[0].anchor = p[1].anchor
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_case_block(self, p):
        '''
        case_block : key NEWLINE INDENT stanzas DEDENT
                   | key scalar NEWLINE
                   | key NEWLINE
        '''
        if len(p) == 6:
            p[0] = ast.Case(p[1], p[4])
        elif len(p) == 3:
            p[0] = ast.Case(p[1], ast.YayScalar(""))
        else:
            p[0] = ast.Case(p[1], p[2])
        self.anchor(p, 1)

    def p_empty(self, p):
        '''
        empty :
        '''
        p[0] = ast.YayDict()
        p[0].anchor = Anchor(self)

    def p_root(self, p):
        '''
        root : DOCUMENT_START document_root
             | EXPRESSION_START expression_root
        '''
        p[0] = p[2]

    def p_document_root(self, p):
        '''
        document_root : stanzas
                      | empty
        '''
        p[0] = p[1]

    def p_expression_root(self, p):
        '''
        expression_root : expression_list
        '''
        p[0] = p[1]

    def p_stanza(self, p):
        '''
        stanza : yaydict
               | yaylist
               | extend
               | directives
               | directive
        '''
        p[0] = p[1]

    def p_stanzas(self, p):
        '''
        stanzas : stanza
                | stanza stanza
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ast.Stanzas(p[1], p[2])
            self.anchor(p, 1)

    def p_stanzas_merge(self, p):
        '''
        stanzas : stanzas stanza
        '''
        p[0] = p[1]
        p[0].append(p[2])

    def p_extend(self, p):
        '''
        extend : EXTEND key scalar NEWLINE
               | EXTEND key NEWLINE INDENT stanzas DEDENT
        '''
        if len(p) == 5:
            value = p[3]
        else:
            value = p[5]
        extend = ast.YayExtend(value)
        p[0] = ast.YayDict([(p[2], extend)])
        self.anchor(p, 1)
        extend.anchor = p[0].anchor

    def p_scalar_emptydict(self, p):
        '''
        scalar : EMPTYDICT
        '''
        p[0] = ast.YayDict()
        self.anchor(p, 1)

    def p_scalar_emptylist(self, p):
        '''
        scalar : EMPTYLIST
        '''
        p[0] = ast.YayList()
        self.anchor(p, 1)

    def p_scalar_value(self, p):
        '''
        scalar : VALUE
        '''
        p[0] = ast.YayScalar(p[1])
        self.anchor(p, 1)

    def p_key(self, p):
        '''
        key : VALUE COLON
        '''
        p[0] = p[1]

    def p_template(self, p):
        '''
        scalar : LDBRACE expression_list RDBRACE
        '''
        p[0] = p[2]
        self.anchor(p, 1)

    def p_scalar_multiline(self, p):
        '''
        scalar : multiline MULTILINE_END
        '''
        p[0] = p[1].to_scalar()

    def p_scalar_merge(self, p):
        '''
        scalar : scalar scalar
        '''
        p[0] = ast.YayMerged.merge(p[1], p[2])
        p[0].anchor = p[1].anchor

    def p_yaydict_keyscalar(self, p):
        '''
        yaydict : key scalar NEWLINE
        '''
        p[0] = ast.YayDict([(p[1], p[2])])
        self.anchor(p, 1)

    def p_yaydict_keystanza(self, p):
        '''
        yaydict : key NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.YayDict([(p[1], p[4])])
        self.anchor(p, 1)

    def p_yaydict_keyblank(self, p):
        '''
        yaydict : key NEWLINE
        '''
        value = ast.YayScalar("")
        p[0] = ast.YayDict([(p[1], value)])
        self.anchor(p, 1)
        value.anchor = p[0].anchor

    def p_multiline(self, p):
        '''
        multiline : MULTILINE scalar NEWLINE
        '''
        p[0] = ast.YayMultilineScalar(p[2], p[1].strip())
        p[0].append(p[3])
        self.anchor(p, 1)

    def p_multiline_merge(self, p):
        '''
        multiline : multiline scalar NEWLINE
        '''
        p[0] = p[1]
        p[0].append(p[2])
        p[0].append(p[3])

    def p_yaydict_merge(self, p):
        '''
        yaydict : yaydict yaydict
        '''
        p[0] = p[1]
        p[0].merge(p[2])

    def p_listitem_scalar(self, p):
        '''
        listitem : HYPHEN scalar NEWLINE
        '''
        p[0] = p[2]
        self.anchor(p, 1)

    def p_listitem_key_newline(self, p):
        '''
        listitem : HYPHEN key NEWLINE INDENT stanzas DEDENT
        '''
        p[0] = ast.YayDict([(p[2], p[5])])
        self.anchor(p, 1)

    def p_listitem_key_scalar(self, p):
        '''
        listitem : HYPHEN key scalar NEWLINE
        '''
        p[0] = ast.YayDict([(p[2], p[3])])
        self.anchor(p, 1)

    def p_listitem_dict(self, p):
        '''
        listitem : HYPHEN key scalar NEWLINE INDENT yaydict DEDENT
        '''
        p[0] = ast.YayDict([(p[2], p[3])])
        p[0].merge(p[6])
        self.anchor(p, 1)

    def p_yaylist(self, p):
        '''
        yaylist : listitem
                | yaylist listitem
        '''
        if len(p) == 2:
            p[0] = ast.YayList(p[1])
            p[0].anchor = p[1].anchor
        elif len(p) == 3:
            p[0] = p[1]
            p[0].append(p[2])

    def p_error(self, p):
        if p is None:
            raise EOFParseError(Anchor(self))
        else:
            anchor = ColumnAnchor(self, p)
            if p.type == 'NEWLINE':
                raise EOLParseError(anchor)
            else:
                raise UnexpectedSymbolError(p, anchor)


class Parser(BaseParser):

    def parse(self, value, source="<unknown>", tracking=True, debug=False):
        value = '\n'.join(value.splitlines(False)) + '\n'
        return super(Parser, self).parse(value, source, tracking, debug)


class ExpressionParser(BaseParser):
    Lexer = ExpressionLexer
