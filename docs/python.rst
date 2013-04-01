======================
Using yay in your code
======================

There are 2 ways to work with the Yay configuration language. The primary method is one that embraces the lazy nature of the configuration language but is still pythonic.

Consider the following configuration::

    network:
        proxy:
            type: socks
            host: 127.0.0.1
            port: 8000

        allowed:
          - 127.0.0.1

You can setup yay to load such a file like so::

    import yay, os
    config = yay.Config(searchpath=[os.getcwd()])
    config.load_uri("example.yay")

You can access keys as attributes::

    proxy_type = config.network.proxy.type

You can also treat it like a dictionary::

    proxy_type = config['network']['proxy']['type']

You can also iterate over them::

    for allowed_ip in config.network.allowed:
        do_stuff(allowed_ip)

It will throw a NoMatching exception if the list isn't defined. If a list is optional you can catch the exception::

    try:
        for allowed_ip in config.network.allowed:
            firewall.add(allowed_ip)
    except errors.NoMatching:
        firewall.deny_all()

All node access is lazy. When you look up a key the object that is returned is a proxy. A promise that when the graph is result the key that you have requested will be returned. You should use this to do strict type checking coercion::

    config.network.proxy.as_int()

This would raise a ``errors.TypeError`` because ``network.proxy`` is a dictionary not an integer.

You can use the more python ``int()``, ``float()`` and ``str()`` operators::

    print "address:", str(config.network.proxy.host)
    print "port:", int(config.network.proxy.port)

However one advantage of the ``node.as_`` form is that you can express defaults in your python code::

    print "address:", config.network.proxy.host.as_string(default='localhost')
    print "port:", config.network.proxy.port.as_int(default=8000)

If your code detects an error in the configuration it can use the anchor property of the node to raise a useful error message::

    proxy_type = config.network.proxy.type
    if not str(proxy_type) in ("socks", "http"):
        print "Incorrect proxy type!"
        print "file:", proxy_type.anchor.source
        print "line:", proxy_type.anchor.lineno
        print "col:", proxy_type.anchor.col

Finally, if you just want to examine your configuration via python simple types you can use the ``yay.load_uri`` and ``yay.load`` API's::

    config = yay.load_uri("example.yay")
    assert isinstance(config, dict)

The disadvantage of this approach is you lose access to line/column metadata for error reporting.
