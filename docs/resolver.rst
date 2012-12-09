=========
Resolving
=========

The language is parsed into a graph.


Parenting
=========

Every node should have one and only one parent. Detached nodes are not valid.
It is the responsibility of the parent to adopt its child nodes and let them
know who there parents are.

Parents will hold a strong ref to their children. Therfore the ref back to the
parent can be a weakref.


Predecessors
============

When a node is inserted into a Mapping it might supercede an existing key. The
graph will keep track of this, which allows mappings to perform operations that
involve previous versions of themselves. For example::

    foo:
      - 1
      - 2

    extend foo:
      - 3

This would parse to:

.. digraph:: foo

    Mapping;
    Mapping -> Extend [label="foo"];
    Sequence1 [label="Sequence"];
    Boxed1 [label="1"];
    Boxed2 [label="2"];
    Sequence1 -> Boxed1;
    Sequence1 -> Boxed2;
    Extend -> Sequence1 [label="predecessor"];
    Sequence2 [label="Sequence"];
    Boxed3 [label="3"];
    Sequence2 -> Boxed3;
    Extend -> Sequence2 [label="inner"];

With this structure it is then easy to combine the original list with the 2nd
list.


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
need to resolve the guard expression. But there is no need to resolve the other
child nodes of If.

In this case, calling expand() will return the predecessor mapping if the
condition is false and the child mapping if it is true. In otherwords, the
condition is resolved but the mapping that is guarded by the condition is not.
We can then access ``default`` without triggering ``dont_resolve_me``.

(#FIXME: I think the correct thing is to return a clone of the child mapping,
but predecessored and parented as though it were the if).

It is important that when a node is expanded the node that it returns is indeed
expanded. To clarify, consider this example::

    var: 1

    % if 0:
        var: 2

    % if 0:
        var: 3

    foo: {{ var }}

If this was parsed and you attempted to expand ``foo`` we'd expect it to return
a ``Boxed(1)``

When the first ``If`` node is expanded it will realise that the condition is
false and attempt to return its predecessor. However it's predecessor is a
``If`` node as well. So if when a node is expanded it returns another existing
node it should take care to call ``expand`` upon it. In this case, the 2nd
``If`` will expand to a ``Mapping`` and when a ``Mapping`` is expanded it will
just return itself. This is the correct behaviour.


Variable expansion
==================

Expressions can reference variables. These might be keys in the global document
or they might be temporary variables in the local scope. An example of this
might be::

    somevar: 123

    foo:
        % let temp1 = 123
        bar: {{ somevar }} {{ temp1 }}

In order to resolve ``bar`` the graph needs to be able to resolve ``temp1`` and
``somevar``.

When a variable is referenced from an expression it is not immediately 'bound'.
This is not the point at which we traverse the graph and find these variables.
Instead we place an ``Access`` node in the graph.

Primarily an ``Access`` node needs to know the key or index to traverse to.
This is an expression that will be resolved when any attempt to expand the node
is actioned. This expression could be as simple as a literal, or as complicated
as something like this::

    {{ foo.bar[1].baz[someothervar[0].bar] else foo.bar[0] }}

When no additional parameters are passed to an Access node it will look up the
key in the current scope (see the Context section).

However you can specify an expression on which to act. This is useful because
you can chain several ``Access`` nodes together. For the example above, the
expression ``{{foo.bar}}`` would be parsed to::

    Access(Access(None, "foo"), "bar")


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
behaviour is that it is always 6 but a context object approach did not allow this.

Another disadvantage of this approach is that a node doesn't resolve to one
state - it resolves to many states as it could be passed many different
contexts. This makes memoization uglier and it caused suspicion that variables
might change as the graph was resolved - this is not supposed to be possible.

The current approach is to treat context as a member of the graph. When an
object wants to look up a name and consider scope it asks its parent for the
nearest context node. This just traverses its parents until it reaches a
context node or reaches the root of the graph. If a context node cannot answer
it's query then traversal continues. When the root of the graph is reached if
no match has been found the ``get`` method is called on the root. This may
raise an exception if there is no such node.


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


