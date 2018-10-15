.. _tutorial/install:

Install
=======

To use a package with Wiz it needs to be available in a registry.
Adding a definition to a registry can be done manually, by either copying the
file to location on the file system (like `~/.wiz/registry`) or commit it to
one of the registries on `Gitlab <http://gitlab/rnd/wiz-registry>`_.

To ease and automise this process an ``install`` command has been added to Wiz::

    >>> wiz install -h

Command line Usage
------------------

Running ``wiz install`` with a definition and a registry will add that
definition to the specified registry and update the ``install-location`` inside
the definition to match the data location it has been installed to.

.. code-block:: console

    >>> wiz install package-0.1.0.json --registry ~/.wiz/registry

    info: Successfully installed definition package-0.1.0.json to ~/.wiz/registry.

.. code-block:: console

    >>> cat ~/.wiz/registry/package-0.1.0.json
    {
        "identifier": "package",
        "version": "0.1.0",
        "description": "Some description.",
        "install-location": "/path/package/package-0.1.0",
        "system": {
            "arch": "x86_64",
            "os": "el >= 7, < 8"
        },
        "environ": {
            "PYTHONPATH": "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
        }
    }

.. hint::

    If the installed data is not in the same directory as the package
    definition, an additonal argument ``--install-location`` can be set to
    the data. This will make sure Wiz can find the installed data
    at runtime.

API Usage
---------

The same result can be achieved using the :term:`Python` API call
:func:`wiz.install_definition`::

    import wiz

    wiz.install_definition(
        definition_path="/path/package-0.1.0.json", registry_location="~/.wiz/registry"
    )
