.. _release/migration:

***************
Migration notes
***************

This section will show more detailed information when relevant for switching to
a new version, such as when upgrading involves backwards incompatibilities.

.. _release/migration/2.0.0:

Migrate to 2.0.0
================

.. rubric:: registries

The following commands have been renamed:

* :option:`--definition-search-paths <wiz --registry>` → :option:`--registry <wiz --registry>`
* :option:`--definition-search-depth <wiz --registry-depth>` → :option:`--registry-depth <wiz --registry-depth>`

The registry paths can now be set as follow::

    wiz -r /path/to/registry1 -r /path/to/registry2 use foo

The :option:`--add-registry <wiz --add-registry>` command has been added in
order to prepend a registry in front of discovered registries.

.. rubric:: installation

The ``wiz install`` sub-command has been modified to regroup the
`--registry-path` and `--registry-id` options into one
:option:`--registry <wiz install --registry>` option which can be used as
follow::

        # For local registries
        >>> wiz install foo.json --registry /path/to/registry
        >>> wiz install foo.json -r /path/to/registry

        # For VCS registries
        >>> wiz install foo.json -registry wiz://primary-registry
        >>> wiz install foo.json -r wiz://primary-registry

The `--install-location` option from the ``wiz install`` sub-command as been
removed as editing the definition can be simply done via the new ``wiz edit``
sub-command.

The optional :ref:`install-root <definition/install_root>` keyword has been
added to define a prefix path to the :ref:`install-location
<definition/install_location>`

.. rubric:: namespaces

The optional :ref:`namespace <definition/namespace>` keyword has been added to
the definition in lieu of the previous "group" keyword which has been removed.

The "group" keyword was only used to precise the folder hierarchy within
``VCS Registry``, whereas :ref:`namespaces <definition/namespace>` are
actively used for the definition query and package extraction process.

.. rubric:: conditions

The optional :ref:`conditions <definition/conditions>` keyword has been added to
indicate a list of packages which must be in the resolution graph for a
definition package to be include.

It replaces the "constraints" keyword as the same logic can be achieved with
:ref:`conditions <definition/conditions>` instead.

With constraint::

    {
        "constraints": [
            "maya ==2016.*"
        ]
    }

With condition::

    {
        "conditions": [
           "maya"
        ],
        "requirements": [
           "maya ==2016.*"
        ]
    }

.. rubric:: implicit packages

Implicit packages identified by the :ref:`auto-use <definition/auto-use>`
keyword are now prepended to the list of explicit requests instead of being
appended. It ensures that implicit packages have always higher priorities than
explicit packages, which is necessary when being used within project registries
to augment or overwrite environment variables.

Consider the following definitions:

.. code-block:: json

    {
       "identifier": "project",
       "auto-use": true,
       "environ": {
          "SHADER_PATH": "/jobs/ads/project/shaders:${SHADER_PATH}"
       }
    }

.. code-block:: json

    {
       "identifier": "mtoa",
       "environ": {
          "SHADER_PATH": "/path/to/mtoa/shaders:${SHADER_PATH}"
       }
    }

The command ``wiz use mtoa`` would previously resolve the :envvar:`SHADER_PATH`
environment variable as follow:
``/path/to/mtoa/shaders:/jobs/ads/project/shaders``

It will now be resolved as follow:
``/jobs/ads/project/shaders:/path/to/mtoa/shaders``

.. rubric:: spawned shell

The "shell_type" optional argument has been removed from :func:`wiz.spawn.shell`
as spawned shell will only support :term:`Bash` for now.

.. rubric:: API

The following functions have been renamed:

* :func:`wiz.package.initiate_environ` → :func:`wiz.environ.initiate`
* :func:`wiz.package.sanitise_environ_mapping` → :func:`wiz.environ.sanitise`

:class:`~wiz.package.Package` can now be instantiated with a simple mapping. A
new :func:`wiz.package.create` function has been added to create packages from
:class:`~wiz.definition.Definition` instances.

:func:`wiz.package.generate_identifier` has been removed as this logic has been
implemented in the following attributes:

* :attr:`wiz.definition.Definition.version_identifier`
* :attr:`wiz.package.Package.identifier`

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
