=========
Resolving
=========

The language is parsed into a graph.

Resolving vs Expanding
======================

The power of Yay is its lazyness. In order to make the language sufficiently
lazy the graph has to avoid resolving any data structues it can until the last
moment.

A simple example is a nested mapping::

    foo:
       bar: {{ some_other_section }}
       baz:
         qux: 1
         quix: 2

You shouldn't need to resolve ``bar`` (and hence the whole of
``some_other_section``). That would rather limit the flexibility of lazy
evaluation.

So mapping nodes can be traversed without needing to resolve the entire graph.
We do this with the ``get`` function::

    graph.get("foo").get("baz").get("quix").resolve() == 2

Things get a bit more complicated when command expression are involved. Let's
consider the ``if`` operation::

    cond: hello
    default: happy

    % if cond == "hello"
        default: really happy
        dont_resolve_me: ${some.datastructure[0].somewhere.else}

The parser will return an If node that has a predecessor mapping. The If node
needs to be traversal friendly. There is no need to resolve the
``dont_resolve_me`` variable when attempting to access ``default``.

This is where the ``expand`` API comes in. In order to resolve ``default`` we
need to resolve the if expression. But there is no need to resolve the other
child nodes of If.

In this case, calling expand() will return the predecessor mapping if the
condition is false and the child mapping if it is true. In otherwords, the
condition is resolved but the mapping that is guarded by the condition is not.
We can then access ``default`` without triggering ``dont_resolve_me``.

(#FIXME: I think the correct thing is to return a clone of the child mapping,
but predecessored and parented as though it were the if).


Context
=======

The language has some variables that are scoped. For example::

    i: 5

    foo:
      % for i in baz
          - {{ i }}

``i`` has different values depending on whether you are inside the for loop or
not.

In early versions of yay context was handled by passing around a context
object. Anytime a node contributed to the context it would push to this context
object. This was problematic::

    i: 5
    b: {{i+1}}

    foo:
      % for i in baz
          - i: {{ i }}
            b: {{ b }}

Is ``b`` always ``6``, or does its value change with the for loop? The correct
behaviour is that it is always 6 but this approach did not allow this.

Another disadvantage of this approach is that a node doesn't resolve to one
state - it resolves to many states as it could be passed many different
contexts. This makes memoization uglier and it caused suspicion that variables
might change as the graph was resolved - this is not supposed to be possible.

The current approach is to treat context as a member of the graph. When an
object wants to look up a name and consider scope it asks its parent for the
nearest context node. This just traverses its parents until it reaches a
context node or reaches the root of the graph. If a context node cannot answer
it's query then traversal continues.

For
===

The expansion of a for loop requires its children to be cloned and parented to
a context node for each iteration of the loop. For example::

    baz:
      - 1
      - 2

    foo:
      % for i in baz
          - {{ i }}

Might expand to something like ``Seq(Ctx({'i':1), Tmpl("{{i}}"), Ctx({'i':2}, Tmpl("{{i}}")))``


