==============
yay ain't YAML
==============

.. image:: https://travis-ci.org/isotoma/yay.png
   :target: https://travis-ci.org/#!/isotoma/yay


Yay is a non-strict lazily evaluated configuration language. It combines
YAML-like data declarations with lazy python expressions.

An example yay file for configuring a load balancer might be::

    lb1:
      backends:
        % for name in ['apple', 'pear']
          - name: {{ name }}
            role: web

      # If we are on in prod, turn on SSL on the LB
      % if environ == 'prod':
          protocol: https


Using yay
=========

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
