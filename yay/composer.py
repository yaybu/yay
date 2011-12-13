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

from yaml.error import MarkedYAMLError
from yaml.events import ScalarEvent, SequenceStartEvent, SequenceEndEvent, \
    MappingStartEvent, MappingEndEvent, AliasEvent, StreamEndEvent

from yay.nodes import *
from yay.parser import Parser
from yay.errors import SyntaxError

class ComposerError(MarkedYAMLError):
    pass


class Composer(object):

    def __init__(self, secret=False):
        self.secret = secret
        self.root = None
        self.parser = Parser(self)

        def define(value, args):
            value.defined_name = args.strip()
            return value

        self.action_map = {
            "define": define,
            "copy": lambda value, args: Copy(value),
            "assign": lambda value, args: value,
            "append": lambda value, args: Append(value),
            "remove": lambda value, args: Remove(value),
            "foreach": lambda value, args: ForEach(self, value, self.parser.foreach_statement.parseString(args)),
            "with": lambda value, args: With(value, *self.parser.as_statement.parseString(args)),
            "select": lambda value, args: Select(value, self.parser.expression.parseString(args)[0]),
            "flatten": lambda value, args: Flatten(value),
            "bind": lambda value, args: Bind(value),
            "secret": lambda value, args: Secret(value),
            }
        self.dirty = False

    def compose(self, previous):
        try:
            return self._compose(previous)
        except MarkedYAMLError, e:
            raise SyntaxError(
                e.problem,
                self.name,
                e.problem_mark.line,
                e.problem_mark.column,
                e.problem_mark.get_snippet()
                )

    def _compose(self, previous):
        # Drop the STREAM-START event.
        self.get_event()

        # Compose a document if the stream is not empty.
        document = None
        if not self.check_event(StreamEndEvent):
            self.get_event() # Drop DOCUMENT-START
            document = self.compose_root_mapping(previous)
            self.get_event() # Drop DOCUMENT-END

        # Ensure that the stream contains no more documents.
        if not self.check_event(StreamEndEvent):
            event = self.get_event()
            raise ComposerError("expected a single document in the stream",
                    document.start_mark, "but found another document",
                    event.start_mark)

        # Drop the STREAM-END event.
        self.get_event()

        return document

    def compose_node(self, previous):
        if self.check_event(AliasEvent):
            raise ComposerError(None, None, "found alias, these arent supported in yay", event.start_mark)

        node = None

        peeked = self.peek_event()

        if self.check_event(ScalarEvent):
            node = self.compose_scalar(previous)
        elif self.check_event(SequenceStartEvent):
            node = self.compose_sequence(previous)
        elif self.check_event(MappingStartEvent):
            node = self.compose_mapping_or_anonymous(previous)

        if not node:
            event = self.peek_event()
            raise ComposerError(None, None, "unexpected event in stream", event.start_mark)

        node.name = self.name
        node.line = peeked.start_mark.line
        node.column = peeked.start_mark.column

        return node

    def compose_scalar(self, previous):
        event = self.get_event()

        if isinstance(event.value, basestring):
            #Icky - this needs to move *beneath* this layer of code
            node = self.parser.templated_string.parseString(event.value)[0]
        else:
            node = self.parser.box(event.value)

        return node

    def compose_sequence(self, previous):
        start = self.get_event()

        data = []
        while not self.check_event(SequenceEndEvent):
            data.append(self.compose_node(None))

        end = self.get_event()

        node = Sequence(data)

        return node

    def handle_imports(self, previous, imports):
        for extend in imports:
            data = self.openers.open(extend)
            secret = hasattr(data, "secret") and data.secret
            previous = self.__class__(data, parent=self.parent, secret=secret).compose(previous)
        return previous

    def handle_special_term(self, previous):
        if self.check_event(MappingEndEvent):
            return previous

        key_event = self.peek_event()
        if key_event.value != self.special_term:
            return previous
        self.get_event()

        special_term = self.compose_node(None).resolve()

        return self.handle_imports(previous, special_term.get("extends", []))

    def compose_mapping_or_anonymous(self, previous):
        start = self.get_event()

        try:
            if not self.check_event(MappingEndEvent):
                if self.peek_event().value.startswith("."):
                    return self.compose_anonymous(previous)
                elif self.peek_event().value.endswith("!"):
                    n = Call(self, self.get_event().value[:-1], self.compose_node(None))
                    return n
            return self.compose_mapping(previous)
        finally:
            self.get_event()

    def compose_anonymous(self, previous):
        # An anonymous expression that doesnt bind to a keyword
        key_event = self.get_event()
        action = key_event.value[1:]

        action_args = None
        if " " in action:
            action, action_args = action.split(" ", 1)

        value = self.compose_node(None)

        assert self.check_event(MappingEndEvent)

        return self.action_map[action](value, action_args)

    def compose_mapping_value(self, container):
        key_event = self.get_event()
        key = key_event.value

        action = "assign"
        if "." in key and key != '.include':
            key, action = key.split(".", 1)

        action_args = None
        if " " in action:
            action, action_args = action.split(" ", 1)

        if action == "define":
            key = ".define"

        try:
            existing = container.get(key)
        except:
            existing = None

        # Grab scalar value
        boxed = self.compose_node(existing)

        # Further box the value based on the kind of action it is
        boxed = self.action_map[action](boxed, action_args)

        # Can't override a locked node
        if existing and existing.locked:
            boxed.error("%s is locked and cannot be overidden" % key)

        # Make sure that Appends are hooked up to correct List
        boxed.chain = existing

        return key, boxed

    def compose_mapping(self, previous):
        container = Mapping(previous)
        while not self.check_event(MappingEndEvent):
            key, value = self.compose_mapping_value(container)
            container.set(key, value)
        return container

    def compose_root_mapping(self, previous):
        if not self.check_event(MappingStartEvent):
            ev = self.get_event()
            #raise ComposerError("Expected root mapping - am denied", ev.start_mark)
            return previous

        start = self.get_event()

        previous = self.handle_special_term(previous)

        previous = Mapping(previous)
        while not self.check_event(MappingEndEvent):
            key, value = self.compose_mapping_value(previous)
            if key == ".include":
                value.set_parent(previous)

                if isinstance(value, Sequence):
                    for i in value.value:
                        i.lock()
                        include = i.resolve()
                        previous = self.handle_imports(previous, [include])
                else:
                    value.lock()
                    includes = value.resolve()

                    if not isinstance(includes, list):
                        value.error("Expected something that resolved to a sequence and didnt")

                    previous = self.handle_imports(previous, includes)

                previous = Mapping(previous)

            elif key == ".define":
                self.parent.definitions[value.defined_name] = value

            else:
                previous.set(key, value)

        end = self.get_event()

        return previous

