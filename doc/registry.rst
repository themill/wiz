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
displayed in the output like this.

.. code-block:: console

    [0] /mill3d/server/apps/WIZ/registry/primary/default
    [1] /mill3d/server/apps/WIZ/registry/secondary/default
    [2] /Users/jeremyr/.wiz/registry

.. _registry/local:

.. rubric:: What are local registries?

A local registry is a simple folder ending on :file:`/path/to/folder/.wiz/
registry`. Definitions can be simply copied into a local registry.

.. _registry/vcs:

.. rubric:: What are VCS registries?

A registry must always be a folder which contain all available definitions.
However, some important registries are stored as a :term:`Gitlab` repository
which automatises the deployment to the file system. A Web API called
:term:`Wiz Vault` is available to release or fetch definitions from these
registries.


The default registries are:

.. _registry/global:

Global registries
=================

Two global registries are available under
:file:`/mill3d/server/apps/WIZ/registry`.

As this folder is part of the weekly sync, it will be identical on all sites.

.. _registry/global/primary:

Primary registry
----------------

The primary registry contains all generic package definitions. If commands are
included, they are in vanilla configuration (no plugins).

This registry is accessable through :term:`Wiz Vault`.

.. seealso::

    http://gitlab.ldn.themill.com/rnd/wiz-registry/primary-registry

.. _registry/global/secondary:

Secondary registry
------------------

The secondary registry contains package definitions for default configurations
(e.g. maya, houdini, nuke, etc). Commands specified here include all the
packages that should be run by default on all sites.

This registry is accessable through :term:`Wiz Vault`.

.. seealso::

    http://gitlab.ldn.themill.com/rnd/wiz-registry/secondary-registry


.. _registry/site:

Site registries
===============

The site registries contain site-specific package definitions, useful
for a single site only (e.g. houdini hsite, site specific environment
variables).

It is available in :file:`/jobs/.wiz/registry/default`.

This registry is accessable through :term:`Wiz Vault`.

.. seealso::

    | http://gitlab.ldn.themill.com/rnd/wiz-registry/london-registry
    | http://gitlab.ldn.themill.com/rnd/wiz-registry/new-york-registry
    | http://gitlab.ldn.themill.com/rnd/wiz-registry/chicago-registry
    | http://gitlab.ldn.themill.com/rnd/wiz-registry/los-angeles-registry
    | http://gitlab.ldn.themill.com/rnd/wiz-registry/bangalore-registry

.. _registry/project:

Project registries
==================

The project registries contain project-specific package definitions (e.g.
containing TD tools currently added via the TDSVN tools). It is parsed depending
on the current directory when running the package manager tool and is located
within a project structure under a :file:`.wiz/registry` sub-folder.

Project registries can only be discovered under :file:`/jobs/ads/`.

.. _registry/personal:

Personal registry
=================

The personal registry contains personal package definitions for development
purposes. It should be located in :file:`~/.wiz/registry`.

.. _registry/setup:

Setting up for Development
==========================

To set up a wiz registry for testing, create a :file:`~/.wiz/registry` directory
in your user directory.
Any :term:`Json` definition in this directory, regardless of hierarchy, will
be picked up by Wiz and can contribute to building the graph.

When developing on multiple registries, they can be set as follows::

    wiz -r {PATH_TO}/registry1 -r {PATH_TO}/registry2 use foo

It is also possible to add a registry to the default one which will result in
the following registry order: :ref:`global <registry/global>`,
:ref:`site <registry/site>`, :ref:`project <registry/project>`,
*custom_registry*, :ref:`personal <registry/personal>`::

    wiz -add {PATH_TO}/custom_registry use foo
