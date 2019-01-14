.. _release/migration:

***************
Migration notes
***************

This section will show more detailed information when relevant for switching to
a new version, such as when upgrading involves backwards incompatibilities.

.. _release/migration/Upcoming:

Migrate to Upcoming
================

The following keywords have been added to the definition schema:

* :ref:`install-root <definition/install_root>`
* :ref:`namespace <definition/namespace>`
* :ref:`conditions <definition/conditions>`

The optional keyword "group" has been removed.

.. _release/migration/1.0.0:

Migrate to 1.0.0
================

The following functions / methods have been removed as part of a refactoring of
the :mod:`wiz.graph` module:

* :func:`wiz.graph.validate_requirements`
* :func:`wiz.graph.extract_requirement`
* :meth:`wiz.graph.Graph.copy`

The :class:`wiz.graph.Graph` constructor only need a :class:`wiz.graph.Resolver`
argument as its content should only rely on the
:meth:`wiz.graph.Graph.update_from_requirements` method.

A "priority" mapping was used in order to identify the shortest path of each
node to the :attr:`root <Graph.ROOT>` level of the graph. However, a node with a
lower "priority" has a higher importance in the graph, which can be confusing.
Therefore the term "priority" has been replaced by "distance". The following
functions have been renamed accordingly:

* :func:`wiz.graph.compute_priority_mapping` → :func:`wiz.graph.compute_distance_mapping`
* :func:`wiz.graph.sorted_from_priority` → :func:`wiz.graph.updated_by_distance`

The following function has also be renamed for clarity:

* :func:`wiz.graph.extract_conflicted_nodes` → :func:`wiz.graph.extract_conflicting_nodes`

The graph division process has been replaced by a function which creates a
:term:`generator iterator` for each graph combination in order to optimize the
resolution process.

.. _release/migration/0.11.0:

Migrate to 0.11.0
=================

The :func:`wiz.export_bash_wrapper` and :func:`wiz.export_csh_wrapper`
functions have been removed and replaced by an :func:`wiz.export_script`
function which simply take a "script_type" argument.

The :func:`wiz.export_definition` function arguments have been updated so that
only a data mapping is required. The "packages" argument which were used to pass
a list of :class:`~wiz.package.Package` instances to indicate the requirements
list is no longer necessary as the requirements list could directly be
passed to the data mapping. This implies that the user no longer need to
fetch the corresponding packages prior to export a definition.

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
