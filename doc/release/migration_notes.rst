.. _release/migration:

***************
Migration notes
***************

This section will show more detailed information when relevant for switching to
a new version, such as when upgrading involves backwards incompatibilities.

.. _release/migration/0.9.0:

Migrate to 0.9.0
================

The following functions have been renamed as part of a refactoring of the
high-level API:

* :func:`wiz.fetch_definitions` → :func:`wiz.fetch_definition_mapping`
* :func:`wiz.query_definition` → :func:`wiz.fetch_definition`
* :func:`wiz.query_current_context` → :func:`wiz.discover_context`
* :func:`wiz.resolve_package_context` → :func:`wiz.resolve_context`

The :func:`wiz.fetch_definition` function has been modified to only return the
definition instance from a package definition request.

The :func:`wiz.discover_context` function does not need any definition mapping
argument as it will be fetched internally.

The :func:`wiz.resolve_command_context` function has been removed. The command
should be resolved independently and the context should be discovered from the
corresponding package request.
