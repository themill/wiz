.. _registry:

****************
Using Registries
****************

.. _registry/introduction:

Introducing Registries
======================

All available package definitions are in one or several registries. If a package
definition is found in several registries, the latest one is picked, which would
imply that the registries are listed in a sensible order to prevent unintuitive
results.

For instance, the order would be:

Global registry:
  It is made available under :file:`/mill3d/server/` and is part of the weekly
  sync to be identical on all sites.

  * Primary

    Contains all generic package definitions. If commands are included, they
    are in vanilla configuration (no plugins).

  * Secondary

    Contains package definitions for default configurations (e.g. maya,
    houdini, nuke, etc). Commands specified here include all the packages
    that should be run by default.

Site registry:
  Contains site-specific package definitions, containing all definitions useful
  for a single site only (e.g. houdini hsite, site specific environment
  variables). It is available in :file:`/jobs/`.

Project registry:
  Contains project-specific package definitions (e.g. containing TD tools
  currently added via the TDSVN tools). It is parsed depending on the current
  directory when running the package manager tool and is located within a
  project structure (under :file:`/jobs/ads/`).

Personal registry:
  Contains personal package definitions for development purposes. It should
  be located in :file:`~/.wiz/registry`.

.. rubric:: Order

When executing Wiz commands, the detected registries and orders will be
displayed in the output like this.

.. code-block:: console

    [0] /Users/jeremyr/dev/rnd/wiz-registry/primary-registry
    [1] /Users/jeremyr/dev/rnd/wiz-registry/secondary-registry
    [2] /Users/jeremyr/.wiz/registry

.. _registry/setup:

Setting up for Development
==========================

To set up a wiz registry for testing, create a :file:`~/.wiz/registry` directory
in your user directory.
Any :term:`Json` definition in this directory, regardless of hierarchy, will
be picked up by Wiz and contributes to building the graph.

However, when developing on multiple registries (like the primary and secondary
global one), it might be beneficial to create a custom :term:`C-Shell` wrapper:

.. code-block:: csh

    #!/bin/tcsh -f
    wiz -dsp {PATH_TO}/primary-registry,{PATH_TO}/secondary-registry $argv
