.. _tutorial/install:

Install
=======

To use a package with Wiz it needs to be available in a registry.

Add definitions manually
------------------------

Adding a definition to a registry can be done manually, either by copying the
file to location on the file system (like ``~/.wiz/registry``) or commit it to
one of the registries on `Gitlab <http://gitlab/rnd/wiz-registry>`_.

When manually adding definitions to a :term:`Gitlab` repository registry, be
sure to tag the commit and push that tag. this will trigger the pipeline to
release the registry to all sites::

    >>> usurp release minor
    >>> git push --follow-tags

Install command
---------------

To ease and automise this process an ``install`` command has been added to Wiz::

    >>> wiz install -h

Running ``wiz install`` with a definition and a registry will add that
definition to the specified registry and update the ``install-location`` inside
the definition to match the data location it has been installed to.

.. hint::

    If the installed data is not in the same directory as the package
    definition, an additonal argument :option:`--install-location
    <wiz install --install-location>` can be set to the data. This will make
    sure Wiz can find the installed data at runtime.

Registry on the file system (untracked)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A registry can be a directory on the file system (ends with ``.wiz/registry``)

.. code-block:: console

    >>> wiz install foo-0.1.0.json --registry-path ~

    info: Successfully installed foo-0.1.0 to ~/.wiz/registry.

The ``install-location`` will be set to where the data is:

.. code-block:: console
    :emphasize-lines: 6

    >>> cat ~/.wiz/registry/foo-0.1.0.json
    {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "Some description.",
        "install-location": "/path/foo/foo-0.1.0",
        "system": {
            "arch": "x86_64",
            "os": "el >= 7, < 8"
        },
        "environ": {
            "PYTHONPATH": "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
        },
        "requirements": [
            "bar >=2, <3",
        ]
    }

The same result can be achieved using the :term:`Python` API call
:func:`wiz.install_definition_to_path`:

    .. code-block:: python

        import wiz

        wiz.install_definition_to_path(
            "/path/foo-0.1.0.json", registry_path="~/.wiz/registry"
        )

Registry repository (tracked)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A registry can be a :term:`Gitlab` repository. To release a definition there,
``wiz install`` can be called with a registry identifier. :term:`Wiz Vault` will
be used to commit the definition to the target registry.

.. code-block:: console

    >>> wiz install foo-0.1.0.json --registry-id primary

    info: Successfully installed foo-0.1.0 to 'primary' registry.

.. code-block:: console
    :emphasize-lines: 7

    >>> wiz view foo==0.1.0 --json
    info: View definition: foo==0.1.0
    {
        "identifier": "foo",
        "version": "0.1.0",
        "description": "Some description.",
        "install-location": "/path/foo/foo-0.1.0",
        "system": {
            "arch": "x86_64",
            "os": "el >= 7, < 8"
        },
        "environ": {
            "PYTHONPATH": "${INSTALL_LOCATION}/lib/python2.7/site-packages:${PYTHONPATH}"
        },
        "requirements": [
            "bar >=2, <3",
        ]
    }

.. hint::

    :term:`Wiz Vault` will take care of commit messages and tags, so once the
    `wiz install` command finishes successfully the changes are automatically
    released without any further action necessary.

The same result can be achieved using the :term:`Python` API call
:func:`wiz.install_definition_to_vault`:

    .. code-block:: python

        import wiz

        wiz.install_definition_to_vault(
            "/path/foo-0.1.0.json", registry_identifier="primary"
        )

Install with requirements
-------------------------

Often packages will have ``requirements``, which have to be installed too.
For this, use :option:`--with-requirements <wiz install --with-requirements>`:

.. code-block:: console

    >>> wiz install foo-0.1.0.json --registry-id primary --with-requirements

    info: Successfully installed definition foo-0.1.0.json to ~/.wiz/registry.
    info: Successfully installed definition bar-2.3.0.json to ~/.wiz/registry.

.. important::

    When installing :option:`--with-requirements
    <wiz install --with-requirements>`, it is important that Wiz can find the
    definitions of all required packages in its `definition-search-paths`.

    The current path is by default added to the `definition-search-paths`, so
    executing the install command in the directory where the definitions are
    located, can ease this process.

    If this is not an option, use the arguments
    :option:`--definition-search-depth <wiz --definition-search-depth>` and
    :option:`--definition-search-paths <wiz --definition-search-paths>`
    to set a path and a search depth to find definitions in.

Using Qip
---------

:term:`Qip` is a tool to install packages into a bundled directory structure.
It will also create Wiz package definitions for any packages that don't include
one already.

Once package data has been installed to their location on the file system, using
:term:`Qip`, ``wiz install`` can be run to install those definitions to a registry.

For this, navigate to the :term:`Qip` package install location on the file
system and run the same install commands as described in the sections above, ie.:

.. code-block:: console

    >>> wiz install foo/foo-0.1.0/foo-0.1.0.json --registry-id primary --with-requirements
