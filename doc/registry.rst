.. _registry:

****************
Using Registries
****************

A registry is a folder which contains one or several :ref:`package definitions
<definition>`. When resolving environments, Wiz will parse these directories to
gather any definitions available and match the requests.

Several registries may be necessary when a :ref:`package definitions
<definition>` should overwrite a command or an entire definition in another
registry.

.. warning::

    A package definition should never overwrite a command or an entire
    definition within a single registry as the discovery order is not
    guaranteed.

When a package definition is found in several registries, the latest one is
picked, which would imply that the registries are listed in a sensible order to
prevent unintuitive results.

When executing Wiz commands, the detected registries and orders will be
displayed in the output as follows:

.. code-block:: console

    [0] /path/to/registry1
    [1] /path/to/registry2
    [2] /path/to/registry3
    ...

We can use :ref:`configuration files <configuration/registry_paths>` to define
default registries.

Other registries can be used when using the command line tool.

.. _registry/discover-implicit:

Discovering implicit registries
-------------------------------

When using the command line tool from a particular location, Wiz will attempt
to discover registries from the current hierarchy structure. It will assume
registries to be in a :file:`.wiz/registry` sub-folder::

    >>> cd /project/shot/animation/
    >>> wiz list package

    Registries
    -----------------
    [0] /project/.wiz/registry
    [1] /project/shot/.wiz/registry
    [2] /project/shot/animation/.wiz/registry

Discovered registries will be added to the list of default registries, if
available. Definitions in the nearest registry will have priority over
definitions deeper down the hierarchy.

It is possible to limit the discovery to a specific folder structure by
specifying a ``discovery_prefix`` in the :ref:`configuration file
<configuration>`:

.. code-block:: toml

    [registry]
    discovery_prefix="/jobs/ads"

Adding a ``discovery_prefix`` will limit the scope of the discovery. In this
example, the registry discovery will be inactive unless the current directory is
under :file:`/jobs/ads` (excluding :file:`/jobs/ads/.wiz/registry`).

The implicit registry discovery feature can be turned off using
:option:`wiz --no-cwd` or by setting this option as a default within a
:ref:`configuration file <configuration>`:

.. code-block:: toml

    [command]
    no_cwd=true

.. note::

    Registries can be discovered via the :term:`Python` API using
    :func:`wiz.registry.discover`.

.. _registry/personal:

Personal registry
-----------------

The personal registry contains personal package definitions for development
purposes. It should be located in :file:`~/.wiz/registry`.

The definitions located in the personal registry have priority over all other
definitions.
