Hacking
=======

Design
------

Yay is a YAML parser extended with lazy-as-possible expression resolving
and simple transformation constructs. The initial version builds upon PyYAML
with additional parsing done by pyparsing (for rapid prototyping). For that
reason it is not a beautiful implementation.

The parser builds a node graph. Calling :py:meth:`yay.nodes.Node.resolve` on the root node causes
all nodes to be transformed into simple types and eventually a mapping will be
returned.

The graph can be partially traversed without triggering any nodes to resolve.
Traversible nodes implement a :py:meth:`yay.nodes.Node.get` function which returns a child from
that key or index. Whatever data is returned will implement the :py:class:`yay.nodes.Node` interface.

Sometimes simplified representations of the graph are required. For example, you
can't access the 5th item of a foreach statement without expanding it. The :py:meth:`yay.nodes.Node.expand`
function performs such simplifications. It will either return ``self`` or it will
return a new object implementing the :py:class:`yay.nodes.Node` interface. Where possible expansion will
avoid resolving child objects.

Languages have local scope. In Yay, we call that context. We look in the context
using the :py:meth:`yay.nodes.Node.get_context` method. By default, we look in the parent :py:class:`yay.nodes.Node`` until
we have found the root of the document (a :py:class:`yay.nodes.Mapping`) and we ask that for a value.
Some :py:class:`yay.nodes.Node` implementations add context. For example, :py:class:`yay.nodes.With`. With basically
aliases a complicated expression to something short to type, for example::

    example.with foo.bar.baz as z:
      - example-${z}-0
      - example-${z}-1
      - example-${z}-2

So how does the node graph know what z is? When a node adds context it literally
adds a :py:class:`yay.nodes.Context` node to the graph, normally during an :py:meth:`yay.nodes.Node.expand`. This object
overrides :py:meth:`yay.nodes.Node.get_context` and may override objects deeper in the graph. The child
of the :py:class:`yay.nodes.Context` node (in the example above, a :py:class:`yay.nodes.Sequence` of strings) will be
resolved against that set of context first and the root of the document second.

Some blocks of Yay markup might need to be evaluated multiple times in different
contexts. An example of this is :py:class:`yay.nodes.ForEach`. Because the context mechanism depends
on parentage (to avoid passing state around and making these methods more cacheable)
we can't reuse the inner Node. The :py:meth:`yay.nodes.Node.expand` method in this case will call
:py:meth:`yay.nodes.Node.clone` and duplicate that node.

When :py:class:`yay.nodes.Node` are created some line and position information is set on them. Any
calls to :py:meth:`yay.nodes.Node.error` will raise an Exception with that metadata set on it.

Nodes
-----

Add a list of nodes here.

