External DataStore Providers
============================

Yay has experimental support for external data sources. You can load them
using ``.bind``.


Using data from Django
----------------------

The expectation is that this feature will let you use yay within a Django
project (perhaps with celery). It does not support using ``django.db`` outside
of a Django project - you need a ``models.py`` and ``settings.py`` and the
normal Django project scaffolding.

You use ``.bind`` to expose your Django model::

    mymodels.bind::
        type: djangostore
        model: myproject.models

Any models defined in ``myprojects.models`` are now available in the
``mymodels`` namespace. When the yay is fully transformed ``mymodels`` won't
be. This is to stop your entire database getting serialized into YAML. However
any values that you use will be fully expanded.

If you were using this with Yaybu you could do things like this::

    resources.foreach user in mymodels.UserProfile:
        - Directory:
            name: /home/${user.name}
            owner: ${user.name}
            group: staff

You can define extra methods on your models and access them through Yay. For
example, if we added this to our UserProfile model::

    class UserProfile(models.Model):

        @classmethod
        def get_leavers(cls):
            return cls.objects.filter(status="left")

You can now use it like this::

    resources.foreach user in mymodels.UserProfile.get_leavers:
        - Directory:
            name: /home/${user.name}
            profile: remove


Importing an existing SQLAlchemy model
--------------------------------------

You can bind to an existing SQLAlchemy model as long as it is on
the python path::

    metadata.bind:
        type: sqlalchemy
        connection: sqlite://
        model: myproject.models

Any tables defined in your schema will now appear as though they
are keys of a metadata mapping.

For example, if your model has a ``users`` table with username
and role pairs, we can select all rows that have a particular role::

    match_role: admin

    ssh_users.foreach u in metadata.users if u.role = match_role:
        username: ${u.name}
        homedir: /home/${u.name}
        fullname: ${u.firstname} ${u.surname}

.. warning::
   Right now filtering is using software fallback - so its
   definitely not suitable for filtering large datasets. It will eventually
   offload filtering to SQLAlchemy, so that yay expressions result in SQL.


You can traverse table joins too. Lets say you had a ``host`` table
and a ``site`` table. Each ``site`` has a ``host_id`` and your SQLAlchemy model
defines a ``sites`` relation on the ``host`` table.

You could do this::

    monitored_urls.foreach h in metadata.hosts:
      .foreach s in h.sites:
        host: ${h.name}
        url: ${s.url}

Obviously this is really contrived. Your model probably has a backref and
this would work foo::

    monitored_urls.foreach s in metadata.sites:
      host: ${s.host.name}
      url: ${s.url}


Defining your model from yay
----------------------------

If your database isn't managed using an existing SQLAlchemy model then
you can just define the model entirely in Yay.

The model we used in the previous example looks like this::

    metadata.bind:
        type: sqlalchemy
        connection: sqlite://
        tables:
          - name: user
            fields:
              - name: id
                type: integer
                pk: True
              - name: username
              - name: password

          - name: service
            fields:
              - name: id
                type: integer
                pk: True
              - name: name
              - name: branch
              - name: host_id
                type: integer
                foreign_key: host.id

          - name: host
            fields:
              - name: id
                type: integer
                pk: True
              - name: name
              - name: services
                relationship: service

The examples of accessing this data should work the same.

