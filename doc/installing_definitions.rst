.. _installing_definitions:

Installing Definitions
======================

A :ref:`definition <definition>` should be available in a :ref:`registry
<registry>` in order to use the corresponding package(s).

The process to install a definition file into a registry depends on the nature
of the registry. A registry can be a *vault* registry or a *local* registry.

.. _installing_definitions/vault:

Installing to vault registries
------------------------------

A registry must always be a folder which contain all available definitions.
However, some important registries are stored as a :term:`Gitlab` repository
which automatize the deployment on the file system. A Web API called
:term:`Wiz Vault` is available to release or fetch definitions from these
registries.

The following registries are *vault* registries:

* :ref:`registry/global/primary`

* :ref:`registry/global/secondary`

* :ref:`registry/site`

:option:`wiz install --registry-id` option can be used to release one or several
definitions in a *vault* registry::

    >>> wiz install /path/to/foo.json --registry-id primary-registry
    >>> wiz install /path/to/definitions/* --registry-id primary-registry

.. warning::

    Releasing a definition within a global registry will affect **ALL** sites.
    Use this command with caution.

A definition can be released into a *vault* registry using the :term:`Python`
API call :func:`wiz.install_definition_to_vault`:

    .. code-block:: python

        wiz.install_definition_to_vault(
            "/path/to/foo-0.1.0.json", "primary-registry"
        )

.. _installing_definitions/local:

Installing to local registries
------------------------------

A local registry is a simple folder with the following extension
:file:`/path/to/folder/.wiz/registry`. Definitions can be safely copied in a
local registry in order to release it.

:option:`wiz install --registry-path` can also be used to release one or several
definitions in a *local* registry::

    >>> wiz install /path/to/foo.json --registry-path /path/to/folder
    >>> wiz install /path/to/definitions/* --registry-path /path/to/folder

.. note::

    You can omit the :file:`.wiz/registry` extension when using this command.

The :ref:`personal registry <registry/personal>` and :ref:`project registries
<registry/project>` are *local* registries. Installing a definition in a
personal registry can be done as follow::

    >>> wiz install /path/to/foo.json --registry-path ~

A definition can be released into a *local* registry using the :term:`Python`
API call :func:`wiz.install_definition_to_path`:

    .. code-block:: python

        wiz.install_definition_to_path(
            "/path/to/foo-0.1.0.json", "/path/to/folder"
        )


.. _installing_definitions/install-location:

Install Location
----------------

The :ref:`install-location <definition/install_location>` value of definitions
can be set during the installation process.
:option:`wiz install --install-location` can be used as follow::

    >>> wiz install . --install-location /path/to/data --registry-path ~
