.. _tutorial/registry:

Registry
========

Introducing Registries
----------------------

All available package definitions are in one or several registries. If a package
definition is found in several registries, the latest one is picked, which would
imply that the registries are listed in a sensible order to prevent unintuitive
results.

For instance, the order would be:

Global registry:
  Contains all generic package definitions (e.g. maya, houdini, nuke, etc.).

Site registry:
  Contains site-specific package definitions (e.g. houdini hsite, site specific
  environment variables).

Project registry:
  Contains project-specific package definitions (e.g. containing TD tools
  currently added via the TDSVN tools).

Personal registry:
  Contains personal package definitions for development purposes.

