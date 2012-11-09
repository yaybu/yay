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

from __future__ import absolute_import

from yay.nodes import Node, BoxingFactory
from yay.errors import NoMatching

from jinja2 import environment, compiler, nodes, runtime


class CodeGenerator(compiler.CodeGenerator):

    in_resolve_expression = False

    def visit_Name(self, node, frame):
        emit_resolve = (self.in_resolve_expression == False)
        self.in_resolve_expression = True

        if node.ctx == 'store' and frame.toplevel:
            frame.toplevel_assignments.add(node.name)
        self.write('l_' + node.name)
        frame.assigned_names.add(node.name)

        if emit_resolve:
            self.write(".resolve()")
            self.in_resolve_expression = True

    def visit_Getattr(self, node, frame):
        emit_resolve = (self.in_resolve_expression == False)
        self.in_resolve_expression = True

        self.write('environment.getattr(')
        self.visit(node.node, frame)
        self.write(', %r)' % node.attr)

        if emit_resolve:
            self.write(".resolve()")
            self.in_resolve_expression = True

    def visit_Getitem(self, node, frame):
        emit_resolve = (self.in_resolve_expression == False)
        self.in_resolve_expression = True

        # slices bypass the environment getitem method.
        if isinstance(node.arg, nodes.Slice):
            self.visit(node.node, frame)
            self.write('[')
            self.visit(node.arg, frame)
            self.write(']')
        else:
            self.write('environment.getitem(')
            self.visit(node.node, frame)
            self.write(', ')
            self.visit(node.arg, frame)
            self.write(')')

        if emit_resolve:
            self.write(".resolve()")
            self.in_resolve_expression = True


class Environment(environment.Environment):

    def _generate(self, source, name, filename, defer_init=False):
        if not isinstance(source, nodes.Template):
            raise TypeError('Can\'t compile non template nodes')
        generator = CodeGenerator(self, name, filename, None, defer_init)
        generator.visit(source)
        return generator.stream.getvalue()


    def resolve(self, name):
        print name
        return self.node.get_root().get(name)

    def getattr(self, obj, attr):
        return obj.get(attr)

    def getitem(self, obj, itm):
        return obj.get(itm)


class Context(runtime.Context):

    def resolve(self, key):
        return self.environment.resolve(key)


class Template(environment.Template):

    def new_context(self, vars=None, shared=False, locals=None):
        return Context(self.environment, self.globals, self.name, self.blocks)


class Jinja(Node):

    def __init__(self, value):
        self.value = value

        self.environment = Environment(
            line_statement_prefix = '%',
            )
        self.environment.node = self

    def expand(self):
        print self.value
        result = self.environment.from_string(self.value, template_class=Template).render()
        # FIXME: Import here to avoid circular import
        from yay import parser
        p = parser.Parser()
        p.input(result)
        node = p.parse()
        node.set_predecessor(self.predecessor)
        return node

    def get(self, idx):
        return self.expand().get(idx)

    def resolve(self):
        return self.expand().resolve()


