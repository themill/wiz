.. _introduction:

************
Introduction
************

Wiz is a package management system. It constructs a requirement graph from a
list a package requests and resolves it into a context mapping which contains
an environment mapping and a command mapping.

The packages are defined in :ref:`package definitions <definition>` which are
stored in one or several :ref:`registries <registry>`.

It is developed in :term:`Python`.

Use :option:`wiz -h` to see all the options.

.. seealso::

    Any design decisions can be followed up on in this
    :ref:`Research document <infinite-monkey:document/package_manager_evaluation>`.
