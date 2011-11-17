Language Tour
=============

Mappings
~~~~~~~~

A mapping is a set of key value pairs. They key is a string and the value
can be any type supported by Yay. All Yay files will contain at least one
mapping::

    site-domain: www.yaybu.com
    number-of-zopes: 12
    in-production: true

You can nest them as well, as deep as you need to. Like in Python, the
relationships between each item is based on the amount of indentation::

    interfaces:
        eth0:
           interfaces: 192.168.0.1
           dhcp: yes

List
~~~~

You can create a list of things by creating an intended bulleted list::

    packages:
        - python-yay
        - python-yaybu
        - python-libvirt

If you need to express an empty list you can also do::

    packages: []

Variable Expansion
~~~~~~~~~~~~~~~~~~

If you were to specify the same Yaybu recipe over and over again you would
be able to pull out a lot of duplication. You can create templates with
placeholders in and avoid that. Lets say you were deploying into
a directory based on a customer project id::

    projectcode: MyCustomer-145

    resources:
        - Directory:
            name: /var/local/sites/${projectcode}

        - Checkout:
            name: /var/local/sites/${projectcode}/src
            repository: svn://mysvnserver/${projectcode}

If you variables are in mappings you can access them using ``.`` as seperator.
You can also access specific items in lists with ``[]``::

    projects:
      - name: www.foo.com
        projectcode: Foo-1
        checkout:
            repository: http://github.com/isotoma/foo
            branch: master

    resources:
        - Checkout:
            repository: /var/local/sites/${projects[0].checkout.repository}

Sometimes you might only want to optionally set variables in your
configuration. Here we pickup ``project.id`` if its set, but fall back
to ``project.name``::

    project:
        name: www.baz.com

    example_key: ${project.id else project.name}


Including Files
~~~~~~~~~~~~~~~

You can import a recipe using the yay extends feature. If you had a template
foo.yay::

    resources:
        - Directory:
              name: /var/local/sites/${projectcode}
        - Checkout:
              name: /var/local/sites/${projectcode}/src
              repository: svn://mysvnserver/${projectcode}

You can reuse this recipe in bar.yay like so::

    .include:
      - foo.yay

    projectcode: MyCustomer-145


Extending Lists
~~~~~~~~~~~~~~~

If you were to speficy resources twice in the same file, or indeed across
multiple files, the most recently specified one would win::

    resources:
        - foo
        - bar

    resources:
        - baz

If you were to do this, resources would only contain baz. Yay has a function
to allow appending to predefined lists: append::

    resources:
        - foo
        - bar

    resources.append:
        - baz

You can also use ``.remove``, which works in a similar way::

    resources:
        - foo
        - bar

    resources.remove:
        - bar

The list now only contains ``foo``.


For Loops
~~~~~~~~~

You might want to have a list of project codes and then define multiple
resources for each item in that list. You would do something like this::

    projectcodes:
        MyCustomer-100
        MyCustomer-72

    resources.append:
        .foreach p in projectcodes:
            - Directory:
                  name: /var/local/sites/${p}
            - Checkout:
                  name: /var/local/sites/${p}/src
                  repository: svn://mysvnserver/${p}

You can also have conditions::

    fruit:
        - name: apple
          price: 5
        - name: lime
          price: 10

    cheap.foreach f in fruit if f.price < 10: ${f}


You might need to loop over a list within a list::

    staff:
      - name: Joe
        devices:
          - macbook
          - iphone

      - name: John
        devices:
          - air
          - iphone

    stuff.foreach s in staff:
      .foreach d in s.devices: ${d}

This will produce a single list that is equivalent to::

    stuff:
      - macbook
      - iphone
      - air
      - iphone

You can use a foreach against a mapping too - you will iterate over its
keys. A foreach over a mapping with a condition might look like this::

    fruit:
      apple: 5
      lime: 10
      strawberry: 1

    cheap.foreach f in fruit if fruit[f] < 10: ${f}

That would return a list with apple and strawberry in it. The list will
be sorted alphabetically: mappings are generally unordered but we want
the iteration order to be stable.


Select
~~~~~~

The select statement is a way to have conditions in your configuration.

Lets say ``host.distro`` contains your Ubuntu version and you want to install
difference packages based on the distro. You could do something like::

    packages.select:
        karmic:
          - python-setuptools
        lucid:
          - python-distribute
          - python-zc.buildout


With
~~~~

If you have a complicated expression and you want to avoid typing it
over and over again you can use the with expression::

    staff:
      john:
        devices:
         - name: ipod
           serial: 1234

    thing.with staff.john.devices[0] as ipod:
      someattr: ipod.serial
      someotherattr: ipod.name


