
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
    ... qux1.copy: ${foo.bar.baz}
    ... """)

And this will give output like::

    >>> config.get()["qux1"]
    [{'qux': 1, 'quux': 2}, {'qux': 3, 'quux': 4}]

