=========
Resolving
=========

The language is parsed into a directed acyclic graph, with each node representing some data or an expression that must be evaluated in order to produce some data. This sections describes in detail the properties of members of this graph structure.


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

.. digraph:: resolver_predecessor

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


Just-in-time visiting
=====================

In order to transform the graph into it's final form we need to perform a series of transformations to the graph.

The standard approach would be a series of transformations performed via the visitor pattern. Each visitor would know one transformation and they would be performed in order. This does approach to graph rewriting does not suit a graph that is as dynamic as ours. To simplify an ``If`` node one might need to have first simplified a ``For`` node. But also vice-versa.

This means that any graph transformation needs to happen just-in-time. Another way of thinking about this is that while a traditional visitor might visit the graph in the order it is parsed, we need to apply the transformations as a depth first exploration of its dependencies.

(FIXME: There are some really icky and hard to qualify things here, really hard to qualify, come back and fix this!)

The main problem with even a depth first visitor is one of context. It becomes harder to know what is appropriate to resolve and how far.

There are essentially 3 target states:

 * Fully resolved - a python simple type like ``str``, ``list`` or ``dict``
 * Folded - a graph safe simple type like ``Boxed``, ``Sequence`` or ``Mapping``
 * Traversible - a graph safe type that is solved enough to allow it to be traversed

These states are more fully explored in the following sections. For now it is enough to know that they are target states. Some graph nodes will be in a 'folded' state from day 1 (like ``Boxed``) and some will be 'traversible' without any transformations (like ``Mapping``). 'Fully resolved' objects will never exist in the graph.

Given these rules what does a visitor look like when it has to make some nodes folded to make them traversible and resolve others to make their dependants foldable?

The simplest solution is that you don't use a visitor at all. Actually for our situation, each node just needs to know how to simplify itself into the various target states and it needs to know what state its dependents need to be in in order to reach its target state.

For example, consider a node that sums 2 dependent graph members::

    class Addition(object):
        def __init__(self, dependentA, dependentB):
            self.a = dependentA
            self.b = dependentB
        def traversible(self):
            self.error(NotTraversible())
        def folded(self):
            # We explicitly fold our dependencies and rely on exceptions to bail out when something is unfoldable
            # This is covered in a later section
            a, b = self.a.fold(), self.b.fold()
            return Boxed(a.resolve() + b.resolve())
        def resolve(self):
            return self.a.resolve() + self.b.resolve()


Expanding (aka Traversible)
===========================

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

Things get a bit more complicated when command expressions are involved. Let's
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


Folding
========

Of course there are some nodes that cannot be simplified. It helps me to think of the Yay graph as an equation. A completely pure graph can be entirely solved to a single value. However (as discussed later in "Native Classes") not all graph members are pure. An extra stage is required to fully support these non-pure elements. We call this the folding step.

When the graph is folded we are essentially doing a traditional constant folding step that a compiler might do to try and generate better code. The graph is resolved to "simple types" like:

 * Boxed
 * Mapping
 * Sequence

I.e. the goal is to remove any of the 'command mode' structures like ``If`` and ``For``. The results are still in graph form - we haven't simplified them to python simple types.

However, non-pure graph members cannot be folded as we cannot know their value without causing side effects. Let's consider a variable ``boxcat`` that will be ``True`` or ``False``. Our input is this::

    foo: True

    % if foo and boxcat:
        bar: baz

The initial parsed form is:

.. digraph:: folding_parsed

    Boxed1 [label="Boxed(True)"]
    Mapping -> Boxed1 [label="foo"];
    If -> Mapping [label="predecessor"];
    If -> And [label="cond"];
    If -> Mapping2 [label="value"];
    Mapping2 [label="Mapping"];
    Mapping2 -> Boxed2 [label="bar"];
    Boxed2 [label="Boxed('baz')"]
    And -> Access1;
    And -> Access2;
    Access1 [label="Access('foo')"]
    Access2 [label="Access('boxcat')"]

The folded form is:

.. digraph:: folding_folded

    Boxed1 [label="Boxed(True)"]
    Mapping -> Boxed1 [label="foo"];
    If -> Mapping [label="predecessor"];
    If -> Access2 [label="cond"];
    If -> Mapping2 [label="value"];
    Mapping2 [label="Mapping"];
    Mapping2 -> Boxed2 [label="bar"];
    Boxed2 [label="Boxed('baz')"]
    Access2 [label="Access('boxcat')"]

The first ``Access`` (to ``foo``) has been simplified away, as has the ``And`` expression. The ``If`` node is still present because it depends on an unknown external value - ``boxcat``. This graph is now as simple as it can be without suffering any side effects.

The implementation might look something like this::

    class And(object):
        def folded(self):
            uleft, uright = True, True
            try:
                left = self.left.folded()
            except CantFold:
                left = self.left
                uleft = True
            try:
                right = self.right.folded()
            except CantFold:
                right = self.right
                uright = True

            if uright and uleft:
                raise CantFold

            elif uright and not uleft:
                if left.resolve():
                    raise CantFold(right)
                else:
                    return Boxed(False)

            elif uleft and not uright:
                if right.resolve():
                    raise CantFold(left)
                else:
                    return Boxed(False)

            else:
                return Boxed(left.resolve() and right.resolve())

Gnarly! But this is just an encapsulation of some really simple rules:

 * If neither side of the ``And`` is a constant then we can't fold
 * If both sides are then we can fold and return ``True`` or ``False`` via a ``Boxed``
 * Otherwise we can fold and resolve the constant side of the expression
   - If it is False then we can short ciruit the dependency on the external value and return ``Boxed(False)``
   - If it is True then we can't fold, but we can simplify and remove both the ``And`` and the constant side of the expression


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


If
==



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

This would parse to:

.. digraph:: resolver_for_unresolved

    Mapping -> For [label="foo"];
    Function [label="Function(range, 2)"];
    For -> Function [label="sequence"];
    For -> Sequence [label="inner"];
    Access [label="Access(key=i)"];
    Sequence -> Access;


This might expand to:

.. digraph:: resolver_for_expanded

    Context0 [label="Context(i=0)"];
    Sequence -> Context0 [label="0"];
    Sequence0 [label="Sequence"];
    Access0 [label="Access(key=i)"];
    Sequence0 -> Access0;
    Context0 -> Sequence0;
    Context1 [label="Context(i=1)"];
    Sequence -> Context1 [label="1"];
    Sequence1 [label="Sequence"];
    Access1 [label="Access(key=i)"];
    Sequence1 -> Access1;
    Context1 -> Sequence1;


Native Classes
==============

You can bind custom code to the yay graph that interfaces with code outside the graph. Code wrapped for consumption by our non-strict graph is called an 'Actor'. (FIXME: This is subject to change, but Actor is better than further complicating terms like 'Node').

By allowing an engineer to bind their side-effect causing code directly to the graph we gain quite a few powerful features:

 * Implicit dependency graph of relationships between actors
 * Implicit ability to parallelize actor side effects (e.g. load balancer with 20 backends - we can deploy those backends in parallel)

However there are consequences:

 * It is impossible to completely validate the graph ahead of time (doing so would require us to actually cause our side effects)

Actor nodes must follow certain rules so that we can maximise the safety of any operations.

It is clear that in order to avoid activating the native code too soon they need to be the laziest kind of graph member. This is the main reason for the folding step.


Incredibly lazy importing
=========================

One feature of yay1 was that imports were immediate but could consume lazy variables. For example::

    .include: cookbook/entrypoints/${foo}.yay

The consequence of this is that ``foo`` was consumed mid-way through loading the config. But it could be overloaded later in the config. So while ``foo`` might have been ``apache`` when the include was processed, it might be ``gunicorn`` by the time the config is fully parsed. The crude work around was that any variable used to satisfy an include would be 'locked'. Any further attempts to modify that variable should be met with horror.

In yay3 we defer parsing until required.

Imagine 2 simple yay documents. The first is ``fr.yay``::

    hello_world: Bonjour!

And the second is ``main.yay``::

    % import {{ language }}.yay
    language: fr

An initial parsing of this might be:

.. digraph:: resolver_import_unfolded

    Import -> Concatenation;
    Concatenation -> Access;
    Concatenation -> Boxed1;
    Boxed1 [label="Boxed('.yay')"];
    Access [label="Access('language')"];
    Mapping -> Import [label="predecessor"];
    Mapping -> Boxed2 [label="language"];
    Boxed2 [label="Boxed('fr')"];

After constant folding this would expand to:

.. digraph:: resolver_import_folded

    Mapping1 [label="Mapping"];
    Mapping2 [label="Mapping"];
    Mapping1 -> Boxed1 [label="hello_world"];
    Boxed1 [label="Boxed('Bonjour!')"];
    Mapping2 -> Mapping1 [label="predecessor"];
    Mapping2 -> Boxed2 [label="language"];
    Boxed2 [label="Boxed('fr')"];

Because we have removed the need to process the import immediately we no longer have complex document locking requirements.


Early Error Detection
=====================

When not using the class feature of yay then early error detection is not
useful. Detecting all errors will cause the graph to be resolved any way, so
might as well be done JIT.

However the current approach for 'nodes with side effects' means that you might
not have even finished syntax checking before you have started mutating an
external system. In this case, any additional checking you can do is worth it.

The topics discussed in this section are currently in the idea stage.
Navigating the graph without triggering premature expansion is tricky.

Type fixing
-----------

One type of analysis that we can perform on the graph is to look at the
predecessors of each node and make sure that the types of fields don't change.
Once a number, always a number.

For these purposes the only types that matter are::

    * Number
    * String
    * List
    * Dict

Some type inference is possible:

 * We know that a foreach will resolve to a list.
 * If a variable resolves to a constant, then we can get its type - we can do
   this without causing resolves in some cases.

However there are problems.

Consider a case like this::

    foo: bar
    qux: quux

    if somexpr:
        foo: []

    qux: fozzle

The only way to be certain if the final config is correct is to resolve
``somexpr``. This could in the worst case actually cause a side effect.

Another possibility is to have speculative type inference: The if knows it
might return a list for ``foo`` or it might have to defer to its predecessor.
However actually implementing that might be difficult...

Schemas
-------

Part of the problem with external sources of information is we don't know what
outputs they have. If we require nodes to declare their inputs and outputs then
we can do additional checking. This is actually what we do with ``Resources``
in yaybu atm - there is a schema system in yaybu.


Future Work
===========

Parallelization
---------------

The goal here would be to maximise the amount of work that is done in parallel. One way to achieve that is to make it OK for a resolve to end prematurely with a ``ResultNotReady`` exception. When that happens the exception would generally be bubbled up to the root node. However containers could try and resolve their other children at this time. A mapping could resolve its other keys. A sequence could resolve siblings of the node that isn't ready. The result of this would be that 'Actor' nodes could perform side effects in parallel.

This probably shouldn't be tied to twisted - we don't want to complicate supporting gevent or blocking use cases.

Online graphs
-------------

Typical simple graphs are run once and then discarded. However with a robust graph API in place we can use yay as a live decision system. Consider an external data source that subscribes to events from ZeroMQ.

    metrics:
        web_load:
            % ZeroMQ
                connect: mq.example.com
                subscribe: {{ cluster.name }}_load_web

    loadbalancer:
        % LoadBalancer
            listen: http
            members:
                % for i in range(load_to_boxen_needed(metrics.web_load))
                    % Compute
                         name: web{{i}}
                         cookbook: entrypoints/web.yay

The relationship between a metric and the number of compute nodes isn't interesting so i've just black-boxed it with a function. This graph is interesting because ``metrics.web_load`` is sourced from ZeroMQ. It can and will change over time and we can potentially have a graph that responds to external changes...

Think about:

 * It's easy enough to have a graph node that listens for changes, but what does that actually do? The graph API is pull based. We can't push a new value down the chain.
 * I think changes that are detected notify the root node.
 * That node will then resolve itself.
 * The number of compute nodes then may or may not be changed based up the external event.


Terminology
===========

The following terms are used in the section, at times without proper thought as to terminology clashes with other yay modules and often with a complete lack of regard for any traditional use of the term.

Node
    An element or member of the solver graph
Predecessor
    An edge (or arc) to an ancestor. Consider key ``foo``. Regardless of how many times you assign a value to it, all of those values are still accessible from the graph by walking the ``predecessor`` edges. Thus a node that has a ``predecessor`` of ``None`` is the oldest version of a key.
Parent
    All but the root node of the graph are contained within a ``parent`` node. 
Actor Node
    A member of the graph that causes external code to be executed - potentially causing side effects.
Expression Node
    A member of the graph that is resolved by performing an expression against other members of the graph. For example, ``1 + 1`` or ``1 + foo``.
Data Node
    Mapping, sequence or literal
Command Node
    A statement block such as ``if`` or ``for``
