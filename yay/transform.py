from yay import parser, ast, errors
import sys
import os
import optparse

try:
    import yaml
except ImportError:
    yaml = None


def graph_to_yaml(opts, graph):
    if not yaml:
        print >>sys.stderr, "Please install PyYAML to use this tool"
        sys.exit(1)

    # Resolve
    try:
        resolved = graph.resolve()
    except errors.Error as e:
        print >>sys.stderr, "A runtime error was captured"
        print >>sys.stderr, str(e)
        sys.exit(1)

    # Dump as YAML
    return yaml.dump(resolved, default_flow_style=False)

def graph_to_dot(opts, graph):
    if opts.phase == "normalized":
        graph = graph.normalize_predecessors()

    return "\n".join(graph.as_digraph())

def graph_to_py(opts, graph):
    import pprint

    try:
        resolved = graph.resolve()
    except errors.Error as e:
        print >>sys.stderr, "A runtime error was captured"
        print >>sys.stderr, str(e)
        sys.exit(1)

    return pprint.pformat(resolved)

def main():
    converters = {
        "dot": graph_to_dot,
        "yaml": graph_to_yaml,
        "py": graph_to_py,
        }

    p = optparse.OptionParser()
    #p.add_option() to set up yaypath?
    p.add_option('-p', '--phase', action="store", default="initial")
    opts, args = p.parse_args()

    if len(args) != 2:
        print >>sys.stderr, "Expected output type and path to a single yay file"
        sys.exit(1)

    if not args[0] in converters:
        print >>sys.stderr, "Output format must be one of: %r" % converters.keys()
        sys.exit(1)

    phases = ("initial", "normalized")
    if not opts.phase in phases:
        print >>sys.stderr, "Phase must be one of: %r" % opts.phase
        sys.exit(1)

    if not os.path.exists(args[1]):
        print >>sys.stderr, "Path '%s' does not exist" % args[0]
        sys.exit(1)

    data = open(args[1]).read()

    p = parser.Parser()

    # Parse
    try:
        graph = ast.Root(p.parse(data))
    except errors.Error as e:
        print >>sys.stderr, "An error occured parsing the first file"
        print >>sys.stderr, str(e)
        sys.exit(1)

    print converters[args[0]](opts, graph)

