.. _installing_definitions:

Installing Definitions
======================

A :ref:`definition <definition>` must be available in a :ref:`registry
<registry>` in order to use the corresponding package(s).

The process to install a definition file into a registry depends on the nature
of the registry. A registry can be a :term:`VCS Registry` or a
:term:`Local Registry`.

.. _installing_definitions/vault:

Installing to VCS registries
-----------------------------

:option:`wiz install --registry-id` option can be used to release one or several
definitions in a :term:`VCS Registry`::

    >>> wiz install /path/to/foo.json --registry-id primary-registry
    >>> wiz install /path/to/definitions/* --registry-id primary-registry

.. warning::

    Releasing a definition within a global registry will affect **ALL** sites.
    Use this command with caution.

A definition can be released into a :term:`VCS Registry` using the
:term:`Python` API call :func:`wiz.install_definition_to_vault`:

    .. code-block:: python

        wiz.install_definition_to_vault(
            "/path/to/foo-0.1.0.json", "primary-registry"
        )

.. hint::

    A definition can be manually added definitions, by just checking out the
    repository.
    After committing the changes, make sure to tag the commit and push the tag.
    This will trigger the pipeline to release the registry to all sites::

        >>> usurp release minor
        >>> git push --follow-tags


.. _installing_definitions/local:

Installing to local registries
------------------------------

:option:`wiz install --registry-path` can also be used to release one or several
definitions in a :term:`Local Registry`::

    >>> wiz install /path/to/foo.json --registry-path /path/to/folder
    >>> wiz install /path/to/definitions/* --registry-path /path/to/folder

.. note::

    You can omit the :file:`.wiz/registry` extension when using this command.

The :ref:`personal registry <registry/personal>` and :ref:`project registries
<registry/project>` are *local* registries. Installing a definition in a
personal registry can be done as follow::

    >>> wiz install /path/to/foo.json --registry-path ~

A definition can be released into a :term:`Local Registry` using the
:term:`Python` API call :func:`wiz.install_definition_to_path`:

    .. code-block:: python

        wiz.install_definition_to_path(
            "/path/to/foo-0.1.0.json", "/path/to/folder"
        )

.. hint::

    A definition can be manually added to a registry by just copying the
    file to location on the file system (like ``~/.wiz/registry``).


.. _installing_definitions/install-location:

Install Location
----------------

The :ref:`install-location <definition/install_location>` value of definitions
can be set during the installation process.
:option:`wiz install --install-location` can be used as follow::

    >>> wiz install . --install-location /path/to/data --registry-path ~
