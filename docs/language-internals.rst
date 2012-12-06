
==================
Language internals
==================

Whitespace and Indentation
==========================

The lexer passes through most symbols unmolested, however it inserts additional <block> and <end> symbols that are not directly present in the input.

These symbols are identified by lexical analysis of indentation whitespace.

for example::

foo:
  bar:
    baz: quux
    
would generate the output::

  <block> <key 'foo'> ':' 
      <block> <key 'bar'> ':' 
          <block> <key 'baz'> ':' <block> <scalar 'quux'> <end>
          <end>
       <end>
  <end>


Data mode vs Command mode
=========================

Each line of the input is either in data mode or command mode

command mode is introduced by the % character, with optional preceding whitespace

In data mode every character is used as-is, unless it is inside a template, see below.

In command mode, the first word of the line following the % is the name of
the command, unless we are creating a new class, which has a shortcut as
below

In command mode everything following the command on that line is an expression.

Literals in expressions must be quoted if they are strings. Numbers are
interpreted as their type and function calls are supported.

Templates
=========

Within {{ }} double braces the contents are interpreted as the names of variables, with the 
addition of an else operator.

{{foo}} - is replaced with the contents of the variable foo

{{foo else bar}} - is replaced with the contents of foo, unless foo is not defined in which case it is replaced with the contents of bar.

If the named variable does not exist and there is no else clause then this is an error.

Backus-Naur productions
=======================


<list> ::= <listitem> <node>
       | <list> <list>
       | '[]'
      
<dict> ::= <key> ':' <node>
       | <dict> <dict>
       | '{}'
      
<node> ::= <block> <value> <end>

<value> ::= <scalar>
          | <dict>
          | <list>
          | <template>
          
<template> ::= [a-z0-9]*'{{' [a-z0-9]+ '}}' [a-z0-9]*

<include-command> ::= '%' 'include' <expr>

<search-command> ::= '%' 'search' <expr>

<for-loop> ::= <block> '%' 'for' <var> [ 'if' <expr> ] 'in' <expr> <node> <end> 

<extend> :: = 'extend' <key> ':' <node>

<configure> ::= 'configure' <key> ':' <node>

<set> ::= '%' 'set' <var> '=' <expr>

<if-block> ::= '%' 'if' <expr> <node> 
                 [ 'elif' <expr> <node> ]* 
                 [ 'else' <node> ]
                 
<select-block> ::= '%' 'select' <expr>
                     [ <key> ':' <node> ]+

<integer> ::= [0-9]+

<float> ::= [0-9]+ '.' [0-9]+

## TODO: QUOTE ESCAPES

<string> ::= '"' [^"]* '"'
           | "'" [^']* '"'

<function-call> ::= <function> '(' <argument>? [ ',' <argument> ]* ')'

<operator> ::= '+'
             | '-'
             | '/'
             | '*'
              
<comparison> ::= '<'
               | '>'
               | '<='
               | '>='
               | '=='
               | '!='
               
<var> ::= [a-zA-Z] [a-zA-Z0-9]+

<expr> ::= <integer>
         | <float>
         | <string>
         | <function-call>
         | <var>
         | <expr> <operator> <expr>
         | <expr> <comparison> <expr>

# TODO Brackets for precedence
# TODO document default precedence rules

<macro-definition> ::= '%' 'macro' <var> <node>

<call> ::= '%' 'call' <var> <node>

<class> ::= '%' 'create' <expr> <node>
          | '%' <var> <node>
          
      