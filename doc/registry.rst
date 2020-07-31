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

.. _registry/discover:

Discovering registries
----------------------

When using the command line tool from a particular location, registries are
being searched from the folder hierarchy under each :file:`.wiz/registry`
sub-folder.

Discovered registries are ordered from the closest to the furthest.

.. _registry/personal:

Personal registry
-----------------

The personal registry contains personal package definitions for development
purposes. It should be located in :file:`~/.wiz/registry`.
