=================================
Extending And Overriding Examples
=================================

Overidding Variables
--------------------

YAY config can be overriden by overlaying multiple files. 

Consider the following example base.yay::

    >>> config.clear()
    >>> config.file("mem://base.yay", """
    ... foo:
    ...     bar:
    ...         baz: 1
    ...         qux: 2
    ...         quux: 3
    ... """)

And you want to update qux to 5. You can overlay custom.yay on top::

    >>> config.file("mem://custom.yay", """
    ... yay:
    ...     extends:
    ...         - mem://base.yay
    ... foo:
    ...     bar:
    ...         qux: 5
    ... """)

Now we open custom.yay::

    >>> config.load_uri("mem://custom.yay")

Look at the output. baz and quux haven't changed, but qux is now 5::

    >>> print config.get()['foo']['bar']['baz']
    1

    >>> print config.get()['foo']['bar']['quux']
    3

    >>> print config.get()['foo']['bar']['qux']
    5


Modifying Lists
---------------

Consider the following base configuration::

    >>> config.clear()
    >>> config.file("mem://base.yay", """
    ... foo:
    ...     - 1
    ...     - 2
    ... bar:
    ...     - 1
    ...     - 2
    ...     - 3
    ... """)

Lets make an overlay that appends to foo and removes from bar::

    >>> config.file("mem://modify-lists.yay", """
    ... yay:
    ...     extends:
    ...         - mem://base.yay
    ... foo.append:
    ...     - 3
    ... bar.remove:
    ...     - 3
    ... """)

Lets load custom.yay::

    >>> config.load_uri("mem://modify-lists.yay")

And our lists should have been updated::

    >>> print config.get()['foo']
    [1, 2, 3]

    >>> print config.get()['bar']
    [1, 2]

