Background
==========

Configuration files come in a vast variety of flavours, customised for
specific needs. These vary from the very, very simple (/etc/resolv.conf for
example) to files written in Turing-complete languages (for example, Django
uses Python).

Configuration file languages have to strike a balance between two competing
goals: simplicity and power.

Simplicity with Power
---------------------

On the one hand yay needs to be simple enough to be used by non-programmers,
on the other it needs to be flexible enough to create complex configuration files.
Yay aims to serve both these needs.

Technical Summary
-----------------

One of our favourite languages for expressing configuration in has been buildout.
Its variable expansion and extends mechanism are wonderful to use. We wanted
a similiar language for Yaybu.

As advanced buildout users we often ran up against 2 big problems.
One is that the base language - ini files - doesn't support sequences and
mappings properly. And its not quite rich enough - despite inheritance and
good variable expansion we still end up duplicating a lot.

Yay is based on YAML syntax, neatly resolving our lack of sequences and mappings.
But pure YAML doesn't offer the same variable expansion, extension and inheritance
we are used to. So we extended it.

Yay is currently evolving - every time a change to our config feels unnatural we
review how we are using Yay and ask if a language change could make it beautiful and
elegant.

