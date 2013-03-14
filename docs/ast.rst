==================
AST Member Objects
==================

.. automodule:: yay.ast


Object type mixins
==================

All walkable objects in the tree must implement the AST interface. A series of mixins and base classes are provided to keep the other node implementations small.

AST
---

.. autoclass:: AST()
   :members:

Scalarish
---------

.. autoclass:: Scalarish()
   :members:

Streamish
---------

.. autoclass:: Streamish()
   :members:

Proxy
-----

.. autoclass:: Proxy()
   :members:


Sequences and sequence operations
=================================

This section describes the classes that are involved in sequence operations. As much as possible these are iterator based to allow use of massive streams of data.

YayList
-------

.. autoclass:: YayList()
   :members:

YayExtend
---------

.. autoclass:: YayExtend()
   :members:

For
---

.. autoclass:: For()
   :members:


Other nodes
===========

Identifier
----------

.. autoclass:: Identifier()
   :members:


Literal
-------

.. autoclass:: Literal()
   :members:

ParentForm
----------

.. autoclass:: ParentForm()
   :members:

ExpressionList
--------------

.. autoclass:: ExpressionList()
   :members:

Power
-----

.. autoclass:: Power()
   :members:

UnaryMinus
----------

.. autoclass:: UnaryMinus()
   :members:

Invert
------

.. autoclass:: Invert()
   :members:

Expr
----

.. autoclass:: Expr()
   :members:

And
---

.. autoclass:: And()
   :members:

Not
---

.. autoclass:: Not()
   :members:

ConditionalExpression
---------------------

.. autoclass:: ConditionalExpression()
   :members:

ListDisplay
-----------

.. autoclass:: ListDisplay()
   :members:

DictDisplay
-----------

.. autoclass:: DictDisplay()
   :members:

KeyDatumList
------------

.. autoclass:: KeyDatumList()
   :members:

KeyDatum
--------

.. autoclass:: KeyDatum()
   :members:

AttributeRef
------------

.. autoclass:: AttributeRef()
   :members:

LazyPredecessor
---------------

.. autoclass:: LazyPredecessor()
   :members:

UseMyPredecessorStandin
-----------------------

.. autoclass:: UseMyPredecessorStandin()
   :members:

Subscription
------------

.. autoclass:: Subscription()
   :members:

SimpleSlicing
-------------

.. autoclass:: SimpleSlicing()
   :members:

ExtendedSlicing
---------------

.. autoclass:: ExtendedSlicing()
   :members:

SliceList
---------

.. autoclass:: SliceList()
   :members:

Slice
-----

.. autoclass:: Slice()
   :members:

Call
----

.. autoclass:: Call()
   :members:

CallCallable
------------

.. autoclass:: CallCallable()
   :members:

ArgumentList
------------

.. autoclass:: ArgumentList()
   :members:

PositionalArguments
-------------------

.. autoclass:: PositionalArguments()
   :members:

KeywordArguments
----------------

.. autoclass:: KeywordArguments()
   :members:

Kwarg
-----

.. autoclass:: Kwarg()
   :members:

TargetList
----------

.. autoclass:: TargetList()
   :members:

ParameterList
-------------

.. autoclass:: ParameterList()
   :members:

DefParameter
------------

.. autoclass:: DefParameter()
   :members:

Sublist
-------

.. autoclass:: Sublist()
   :members:

YayDict
-------

.. autoclass:: YayDict()
   :members:

YayScalar
---------

.. autoclass:: YayScalar()
   :members:

YayMerged
---------

.. autoclass:: YayMerged()
   :members:

Stanzas
-------

.. autoclass:: Stanzas()
   :members:

Directives
----------

.. autoclass:: Directives()
   :members:

Include
-------

.. autoclass:: Include()
   :members:

Search
------

.. autoclass:: Search()
   :members:

Configure
---------

.. autoclass:: Configure()
   :members:

Set
---

.. autoclass:: Set()
   :members:

If
--

.. autoclass:: If()
   :members:

ElifList
--------

.. autoclass:: ElifList()
   :members:

Elif
----

.. autoclass:: Elif()
   :members:

Select
------

.. autoclass:: Select()
   :members:

CaseList
--------

.. autoclass:: CaseList()
   :members:

Case
----

.. autoclass:: Case()
   :members:

Create
------

.. autoclass:: Create()
   :members:

Macro
-----

.. autoclass:: Macro()
   :members:

CallDirective
-------------

.. autoclass:: CallDirective()
   :members:

Template
--------

.. autoclass:: Template()
   :members:

Context
-------

.. autoclass:: Context()
   :members:

ListComprehension
-----------------

.. autoclass:: ListComprehension()
   :members:

ListFor
-------

.. autoclass:: ListFor()
   :members:

ListIf
------

.. autoclass:: ListIf()
   :members:

Comprehension
-------------

.. autoclass:: Comprehension()
   :members:

CompFor
-------

.. autoclass:: CompFor()
   :members:

CompIf
------

.. autoclass:: CompIf()
   :members:

GeneratorExpression
-------------------

.. autoclass:: GeneratorExpression()
   :members:

DictComprehension
-----------------

.. autoclass:: DictComprehension()
   :members:

SetDisplay
----------

.. autoclass:: SetDisplay()
   :members:

StringConversion
----------------

.. autoclass:: StringConversion()
   :members:

LambdaForm
----------

.. autoclass:: LambdaForm()
   :members:

Comment
-------

.. autoclass:: Comment()
   :members:
