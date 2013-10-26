# Copyright 2013 Isotoma Limited
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

from __future__ import print_function

from yay import parser, config, errors
import sys
import os
import optparse

try:
    import yaml
except ImportError:
    yaml = None


def graph_to_yaml(opts, graph):
    if not yaml:
        print("Please install PyYAML to use this tool", file=sys.stderr)
        sys.exit(1)

    # Resolve
    try:
        resolved = graph.resolve()
    except errors.Error as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Dump as YAML
    return yaml.safe_dump(resolved,
                          default_flow_style=False)


def graph_to_dot(opts, graph):
    if opts.phase == "normalized":
        graph = graph.normalize_predecessors()

    return "\n".join(graph.as_digraph())


def graph_to_py(opts, graph):
    import pprint

    try:
        resolved = graph.resolve()
    except errors.Error as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    return pprint.pformat(resolved)


usage = """\
usage: %prog [options] [filename]

Where output is one of "dot", "yaml" or "py"\
"""


def main(argv=sys.argv[1:], stdin=sys.stdin):
    converters = {
        "dot": graph_to_dot,
        "yaml": graph_to_yaml,
        "py": graph_to_py,
    }

    phases = ("initial", "normalized")
    p = optparse.OptionParser(usage=usage)
    p.add_option('-p', '--phase', action="store",
                 default="initial", help="phase, one of %s" % ",".join(phases))
    p.add_option('-f', '--format', action="store", default="yaml",
                 help="output format, one of: %s. defaults to 'yaml'" % ", ".join(converters.keys()))
    opts, args = p.parse_args(argv)

    if len(args) == 0:
        instream = stdin
        source = "<stdin>"
        searchpath = []
    elif len(args) == 1:
        if not os.path.exists(args[0]):
            print("Path '%s' does not exist" % args[0], file=sys.stderr)
            sys.exit(1)
        instream = open(args[0])
        source = args[0]
        searchpath = [os.path.realpath(os.path.dirname(args[0]))]
    else:
        p.print_usage()
        sys.exit(1)

    if not opts.format in converters:
        print("Output format must be one of: %r" %
              converters.keys(), file=sys.stderr)
        sys.exit(1)

    if not opts.phase in phases:
        print("Phase must be one of: %r" % opts.phase, file=sys.stderr)
        sys.exit(1)

    p = parser.Parser()
    root = config.Config(searchpath=searchpath)

    # Parse
    try:
        root.load(instream, name=source)
    except errors.Error as e:
        print(str(e))
        sys.exit(1)

    print(converters[opts.format](opts, root))
