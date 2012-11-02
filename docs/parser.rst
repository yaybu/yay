
The yay parser does *not* support the full suite of yaml features, only a small subset that is suitable for this problem domain.


Lexer
=====

Each line can consist of:

 1. completely whitespace. this is discarded.
 2. define a new top-level term, optionally with a scalar value. In this case the term is processed and the indentation memory discarded.
 3. define a new non-top-level term, optionally with a scalar value, with an indent level previously seen. In this case appropriate BLOCK and ENDBLOCK symbols are emitted to achieve the desired level 
 
 
Examples
--------

Input::

    foo: bar

    baz: quux

becomes::

    BLOCK KEY(foo) BLOCK VALUE(bar) ENDBLOCK KEY(baz) BLOCK VALUE(quux) ENDBLOCK ENDBLOCK
    

Input::

    foo: bar
         wibble
         wobble

    baz: quux

becomes::
    BLOCK KEY(foo) BLOCK VALUE(bar) VALUE(wibble) VALUE(wobble) ENDBLOCK KEY(baz) BLOCK VALUE(quux) ENDBLOCK ENDBLOCK
    
Input::

    foo: bar
         wibble: wobble

    baz: quux

becomes::
    BLOCK KEY(foo) BLOCK VALUE(bar) KEY(wibble)  BLOCK VALUE(wobble) ENDBLOCK ENDBLOCK KEY(baz) BLOCK VALUE(quux) ENDBLOCK ENDBLOCK

Input::

    foo: bar
         wibble:
             - a
             - b
             - c

becomes::
    BLOCK KEY(foo) BLOCK VALUE(bar) KEY(wibble) BLOCK LISTVALUE(a) LISTVALUE(b) LISTVALUE(c) ENDBLOCK ENDBLOCK KEY(baz) BLOCK VALUE(quux) ENDBLOCK ENDBLOCK

Input::

    foo:
        bar: 
          baz:
            quux: qux
        wibble: wobble
        
becomes::

    BLOCK 
    KEY(foo) 
        BLOCK 
        KEY(bar) 
            BLOCK 
            KEY(quux) 
                BLOCK 
                VALUE(qux) 
                ENDBLOCK 
            ENDBLOCK 
            KEY(wibble) 
                BLOCK 
                VALUE(wobble) 
                ENDBLOCK 
            ENDBLOCK 
        ENDBLOCK
    ENDBLOCK
                    
            