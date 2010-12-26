
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.resolver import Resolver

from yaml.nodes import MappingNode

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

class Constructor(SafeConstructor):

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_mark)
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise ConstructorError("while constructing a mapping", node.start_mark,
                        "found unacceptable key (%s)" % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value

        return mapping

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

Constructor.add_constructor(
        u'tag:yaml.org,2002:map',
        Constructor.construct_yaml_map)


class Loader(Reader, Scanner, Parser, Composer, Constructor, Resolver):

    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)

