What are the semantics for copy?
--------------------------------

How about file1.yay::

    >>> config.file("mem://file1.yay", """
    ... foo:
    ...     bar:
    ...         - baz
    ...         - qux
    ... """)

And file2.yay::

    >>> config.file("mem://file2.yay", """
    ... zop.copy: foo[bar]
    ... """)

And file3.yay::

    >>> config.file("mem://file3.yay", """
    ... yay:
    ...     extends:
    ...         - mem://file1.yay
    ...         - mem://file2.yay
    ... foo:
    ...     bar:
    ...         - x
    ... """)

What will be the output of that?::

    >>> config.load_uri("mem://file3.yay")
    >>> config.get()
    {'zop': ['x'], 'foo': {'bar': ['x']}, 'yay': {'extends': ['mem://file1.yay', 'mem://file2.yay']}}

And clean up (FIXME: Move this in to test_edgecases.py as a tearDown)::

   >>> config.clear()

