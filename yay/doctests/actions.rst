
=======
Actions
=======

You can refer to other sections using the same notation as when formatting a string::

    >>> config.clear()
    >>> config.load("""
    ... foo:
    ...     bar:
    ...         baz:
    ...             - qux: 1
    ...               quux: 2
    ...             - qux: 3
    ...               quux: 4
    ... qux1.copy: foo[bar][baz][1]
    ... """)

And this will give output like::

    >>> config.get()["qux1"]
    {'qux': 3, 'quux': 4}

Of course you can then modify the copy and add extra fields::

    >>> config.load("""
    ... qux1:
    ...     foo: 1
    ... """)

And you will now see::

    >>> config.get()["qux1"]
    {'qux': 3, 'foo': 1, 'quux': 4}

