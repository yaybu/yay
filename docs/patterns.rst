Configuration Patterns
======================

How do i influence the order my recipes execute in?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have a recipe where you want a resource to be inserted near the end
of the resources list, but your recipe is included too early to do that.
What can you do?

The resources list is a normal yay variable so we can exploit the variable
expansion and split your cookbooks in to phases::

    deployment: []
    finalization: []

    resources.flatten:
        - ${deployment}
        - ${finalization}

Instead of appending to resources in your recipes you'd now append to
deployment. If you need to move something to the end of execution
you can add it to the finaliztion list.

