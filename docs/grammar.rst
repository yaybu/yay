
============
Introduction
============

The YAY grammar is based on Python, with additional productions to provide
for the data language stanzas that surround and enclose the pythonic terms.
The data language resembles YAML, but it does not implement much of the
complexity of YAML, which we consider unnecessary for this use case.

The lexer and parser are implemented using PLY.

===========
The Scanner
===========

Input text is tokenised by a stateful lexer. It is a relatively traditional
sort of scanner, except for the interpretation of leading whitespace. Leading
whitespace is processed and consumed using a generator chain, to yield INDENT
and DEDENT symbols as necessary. Other whitespace outside string literals is
eliminated entirely from the output sequence.

The scanner has six states that drastically change how input text is interpreted.

 INITIAL
  In this state the scanner is looking for keys in the YAML-like data language, or for reserved words that indicate the line is pythonic.
 VALUE
  A key has been emitted and the scanner is now looking for a value.
 LISTVALUE
  We are parsing a list of values, each introduced with a '-'
 TEMPLATE
  We are within a template (i.e. {{ }}) and so should emit everything read as-is
 COMMAND
  We are within a "command", i.e. a line of something pythonic
 BLOCK
  We are within a multiline literal block
  
===========
Productions
===========

The docstrings in parser.py provide the productions themselves, in the syntax
required by PLY. Here we summarise the productions in a slightly more typical
syntax, and without the NEWLINE, INDENT and DEDENT symbols that are vital for
parsing but only get in the way when trying to understand the grammar.
 

Python
======

The parser implements virtually all of the Expressions defined for Python:

http://docs.python.org/2/reference/expressions.html

As well as many of the compound statements:

http://docs.python.org/2/reference/compound_stmts.html

Data Language
=============

In addition to these are the data language itself:

Stanzas
-------

The root of a document consists of zero or more stanzas. Each stanza is one of::

  stanza ::= yaydict
           | yaylist
           | extend
           | directives
            
Extend
------

An extend looks like::

  extend ::= "extend" key ":" scalar 
           | "extend" key ":" stanzas

Scalars
-------

A scalar is basically a VALUE read from the data language, or more than one
value. It also handles literal empty dictionaries and merges multiline
symbols from the scanner.

 scalar ::= "{}"
          | "[]"
          | value
          | "{{" expression_List "}}"
          | multiline
          | scalar+
          
Dictionaries
------------
            
These provide the mapping objects in the language::

 yaydict ::= key ":" scalar
           | key ":" stanza
           | key ":"
           | yaydict+ 
           
Lists
-----

These provide the sequence objects in the language::

  yaylist ::= listitem+
            
  listitem ::= "-" scalar
             | "-" key ":" scalar
             | "-" key ":" stanza+
             | "-" key ":" scalar yaydict
             
The last three productions above handle the complex case of a dictionary as a list item.

Directives
----------

Python's compound statements are called "Directives" within YAY. In addition
to the standard python compound statements, YAY introduces a number of it's
own directives::

  directive ::= include_directive
              | search_directive
              | new_directive
              | prototype_directive
              | for_directive
              | set_directive
              | if_directive
              | select_directive
              | macro_directive
              | call_directive
              
Include
~~~~~~~

The include directive includes another file at this point in the input text::

  include_directive ::= "include" expression_list
  
Search
~~~~~~

This adds components to the search path::

  search_directive ::= "search" expression_list

Prototype
~~~~~~~~~

Prototype defines a structure to be reused later::

  prototype_directive ::= "prototype" expression_list ":" stanza+
  
New
~~~

New uses a previously defined prototype::

  new_directive ::= "new" expression_list ":" stanza+
                  | "new" expression_list "as" identifier ":" stanza+
                  
              
For
~~~

This works like a python for statement::

  for_directive ::= "for" target_list "in" expression_list ":" stanza+
                  | "for" target_list "in" or_test "if" expression ":" stanza+
                  
Set
~~~

Set allows temporary local variables to be used, without them appearing in the output graph as data symbols.

  set_directive ::= "set" target_list "=" expression_list
  
If
~~
            
If resembles the python conditional::

  if_directive ::= "if" expression_list ":" stanza+ ("else:" stanza+)?
                 | "if" expression_list ":" stanza+ ("elif" expression_list ":" stanza+)+ ("else:" stanza+)?
                 
Select
~~~~~~

Select implements the select statement familiar from many other languages,
but not present in Python. This is not required in Python, but is a common
requirement in Yay::

  select_directive ::= "select" expression_list ":" (key ":" stanza+)+
  
Macro
~~~~~

Macros are similar to prototypes, in that they allow for simple reuse. See
the language documentation to understand how to use them::

  macro_directive ::= "macro" target_list ":" stanza+
  
Call
~~~~

Call invokes previously defined macros::

  call_directive ::= "call" target_list ":" stanza+
  
