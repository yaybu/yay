Language Tour
=============

Comments
~~~~~~~~

# comment

foo:
   - a
   # foo
   - b

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

Empty mappings
##############

::

packages: {}

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
            name: /var/local/sites/{{projectcode}}

        - Checkout:
            name: /var/local/sites/{{projectcode}}/src
            repository: svn://mysvnserver/{{projectcode}}

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
            repository: /var/local/sites/{{projects[0].checkout.repository}}

Sometimes you might only want to optionally set variables in your
configuration. Here we pickup ``project.id`` if its set, but fall back
to ``project.name``::

    project:
        name: www.baz.com

    example_key: {{ project.id|default(project.name) }}


Large templates
~~~~~~~~~~~~~~~

::

foo j2:
    % for p in projectcodes:
        - Directory:
              name: /var/local/sites/{{p}}
        - Checkout:
              name: /var/local/sites/{{p}}/src
              repository: svn://mysvnserver/{{p}}
    % endfor

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
to allow appending to predefined lists: extend::

    resources:
        - foo
        - bar

    resources extend:
        - baz


For Loops
~~~~~~~~~

You might want to have a list of project codes and then define multiple
resources for each item in that list. You would do something like this::

    projectcodes:
        MyCustomer-100
        MyCustomer-72

    resources extend j2:
        % for p in projectcodes:
            - Directory:
                  name: /var/local/sites/{{p}}
            - Checkout:
                  name: /var/local/sites/{{p}}/src
                  repository: svn://mysvnserver/{{p}}
        % endfor


Including Files
~~~~~~~~~~~~~~~

You can import a recipe using the yay extends feature. If you had a template
foo.yay::

    resources:
        - Directory:
              name: /var/local/sites/{{projectcode}}
        - Checkout:
              name: /var/local/sites/{{projectcode}}/src
              repository: svn://mysvnserver/{{projectcode}}

You can reuse this recipe in bar.yay like so::

    yay include:
        - foo.yay
        - bar.yay

    projectcode: MyCustomer-145


Search path
~~~~~~~~~~~

yay search:


Configuring your environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

yay config:

