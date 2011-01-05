yay ain't YAML
==============

yay is a configuration file format built on top of YAML based on our experience with the ConfigParser extensions buildout uses. It adds overlays (one config file including and extending another) and variables.

Consider a config file that looks something like this::

    foo:
        bar:
            baz:
                - 1
                - 2
                - 3
        qux: wibble.wobble
        quux: wobble

    goo:
        bar:
            baz:
                - 1
                - 2
                - 3
                - 4
        qux: wibble.cobble
        quux: cobble

    hoo:
        bar:
            baz:
                - 1
                - 3
        qux: wibble.yobble
        quux: yobble

With yay, this might look like this::

    foo:
        bar:
            baz:
                - 1
                - 2
                - 3
        qux: wibble.{:quux}
        quux: wobble

    goo.copy: foo
    goo:
        bar:
            baz.append:
                - 4
        quux: cobble

    hoo.copy: foo
    hoo:
        bar:
            baz.remove:
                - 2
        quux: yobble

Using yay
---------

To load yay config from a string you can use the 'load' function::

    >>> from yay import load
    >>> load("""
    ... foo:
    ...     bar: 1
    ... """)
    {"foo": {"bar": 1}}

If you want to load from a URI (file:// and http:// are supported) then use 'load_uri'::

    >>> from yay import load_uri
    >>> load_uri("/etc/someconfig.yay")
    {"foo": {"bar": 1}}

The return value in both cases is a standard python dictionary.
