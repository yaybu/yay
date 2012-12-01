
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
          
<template> ::= [a-z0-9]+ '{{' [a-z0-9]+ '}}' [a-z0-9]+

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
               
<var> ::= [a-z] [a-z0-9]+

<expr> ::= <integer>
         | <float>
         | <string>
         | <function-call>
         | <expr> <operator> <expr>
         | <expr> <comparison> <expr>
         
<macro-definition> ::= '%' 'macro' <var> <node>

<call> ::= '%' 'call' <var>


                     
