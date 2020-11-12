.. _release/release_notes:

*************
Release Notes
*************

.. release:: 3.6.1
    :date: 2020-11-02

    .. change:: fixed

        Updated :func:`wiz.logging.initiate` to ensure that default logging
        :data:`~wiz.logging.PATH` exists so the file handler can be configured
        without raising an error.

.. release:: 3.6.0
    :date: 2020-11-01

    .. change:: changed

        Updated repository to use built-in :mod:`logging` module instead of
        `sawmill <https://gitlab.com/4degrees/sawmill>`_ as there are no clear
        advantages in using a non-standard framework to handle logging.

    .. change:: new

        Added :func:`wiz.logging.initiate` to configure logging for the command
        line tool using a :data:`default configuration
        <wiz.logging.DEFAULT_CONFIG>` which can be modified from the Wiz
        configuration.

        .. seealso:: :ref:`configuration/logging`

    .. change:: changed

        Updated ``wiz analyze`` to make results more condensed and easier to
        use for debugging.

        .. code-block:: console

            >>> wiz analyze

            Metrics                 Values
            ---------------------   -------
            Total                   120
            Errors                  0
            Warnings                2
            With version dropdown   1
            ≥ 5 combination(s)      1
            ≥ 1 second(s)           0
            Max resolution time     0.5484s
            Max combinations        12
            Max version dropdown    5

        Expanded results can be displayed by using
        :option:`wiz analyze -V/--verbose <wiz analyze -V>`.

    .. change:: changed

        Removed :func:`wiz.validate_definition` as it is using unsafe logic
        which modifies the logging configuration outside of the main program.
        This feature will be accessible from ``wiz analyze``  command only.

.. release:: 3.5.2
    :date: 2020-10-30

    .. change:: fixed

        Updated :meth:`wiz.graph.Combination.discover_combinations` to always
        copy the combination before attempting to downgrade conflicting package
        versions, so that it can be safely reused to downgrade other conflicting
        package versions if necessary.

.. release:: 3.5.1
    :date: 2020-10-29

    .. change:: fixed

        Updated :func:`wiz.graph._combined_requirements` to return requirement
        including combined variant identifiers from incoming parents.

    .. change:: fixed

        Updated :meth:`wiz.graph.Graph.downgrade_versions` to preserve the
        same variant identifier when downgrading versions.

.. release:: 3.5.0
    :date: 2020-10-29

    .. change:: changed

        Updated :mod:`wiz.graph` to make the following functions private:

        * :func:`wiz.graph._compute_distance_mapping`
        * :func:`wiz.graph._generate_variant_permutations`
        * :func:`wiz.graph._compute_conflicting_matrix`
        * :func:`wiz.graph._combined_requirements`
        * :func:`wiz.graph._extract_conflicting_requirements`

    .. change:: changed

        Updated :func:`wiz.graph._generate_variant_permutations` to discard
        permutations containing variant nodes with conflicting requirements.
        Previously, the resolver had to consider all conflicting permutations
        before attempting to :meth:`discover
        <wiz.graph.Resolver.discover_combinations>` new combinations by
        :meth:`downgrading <wiz.graph.Graph.downgrade_versions>` the versions
        of conflicting nodes.

    .. change:: changed

        Updated :meth:`wiz.graph.Graph.relink_parents` to record errors as
        :exc:`~wiz.exception.GraphConflictsError` exception which can be raised
        during the :meth:`validation <wiz.graph.Combination.validate>` of a
        combination. This allows the resolver to :meth:`discover
        <wiz.graph.Resolver.discover_combinations>` new combinations by
        :meth:`downgrading <wiz.graph.Graph.downgrade_versions>` the versions
        of the conflicting nodes involved if necessary.

.. release:: 3.4.0
    :date: 2020-10-23

    .. change:: changed

        Updated :func:`wiz.resolve_context` logic to only guess :ref:`namespaces
        <definition/namespace>` from initial requirements without taking
        :ref:`implicit packages <definition/auto-use>` into account.

        .. seealso::

            https://github.com/themill/wiz/issues/60

    .. change:: changed

        Updated :meth:`wiz.graph.Resolver.compute_packages` and
        :class:`wiz.graph.Graph` to take initial namespace counter as a keyword
        argument. This is necessary as the logic handling :ref:`namespace
        <definition/namespace>` frequency counting from initial requirements
        have been moved upstream.

    .. change:: new

        Added :func:`wiz.utility.compute_namespace_counter` to compute a
        :ref:`namespace <definition/namespace>` frequency counter from a list
        of requirements.

.. release:: 3.3.1
    :date: 2020-10-22

    .. change:: fixed

        Reverted :exc:`wiz.exception.DefinitionsExist` to using definition
        labels instead of definitions instances for convenience as
        :ref:`installer plugin <plugins/default/installer>` might not have
        access to the entire definition data when raising the error.

.. release:: 3.3.0
    :date: 2020-10-21

    .. change:: new

        Added the following commands to limit the maximum number of attempts to
        resolve a context before raising an error:

        * :option:`wiz use -ma/--max-attempts <wiz use -ma>`
        * :option:`wiz run -ma/--max-attempts <wiz run -ma>`

    .. change:: new

        Added the following commands to limit the maximum number of combinations
        which can be generated from conflicting variants during the context
        resolution process:

        * :option:`wiz use -mc/--max-combinations <wiz use -mc>`
        * :option:`wiz run -mc/--max-combinations <wiz run -mc>`

    .. change:: changed

        Updated :func:`wiz.resolve_context` to add keyword arguments which
        provide a maximum number of attempts to resolve a context before raising
        an error, and a maximum number of combinations which can be generated
        from conflicting variants during the context resolution process.

    .. change:: changed

        Updated :class:`wiz.graph.Resolver` constructor to add keyword arguments
        which provide a maximum number of resolution attempts before raising
        an error, and a maximum number of combinations which can be generated
        from conflicting variants.

    .. change:: changed

        Refactored :mod:`wiz.graph` to provide a better `separation of concerns
        <https://en.wikipedia.org/wiki/Separation_of_concerns>`_ between stages
        of the resolution process.

        The :class:`~wiz.graph.Resolver` class handles the creation of the
        initial :class:`~wiz.graph.Graph` and the extraction and management of
        :class:`~wiz.graph.Combination` instances. The newly added
        :class:`~wiz.graph.Combination` class handles the version conflict
        resolution, the graph validation and the packages extraction.

    .. change:: changed

        Removed the following functions to improve code readability and move
        logic into different callbacks:

        +----------------+----------------------------------------------------+
        | Removed        | * :func:`wiz.graph.generate_variant_combinations`  |
        +----------------+----------------------------------------------------+
        | Logic moved to | * :meth:`wiz.graph.Resolver.extract_combinations`  |
        +----------------+----------------------------------------------------+

        +----------------+----------------------------------------------------+
        | Removed        | * :func:`wiz.graph.trim_unreachable_from_graph`    |
        |                | * :func:`wiz.graph.trim_invalid_from_graph`        |
        +----------------+----------------------------------------------------+
        | Logic moved to | * :meth:`wiz.graph.Combination.prune_graph`        |
        +----------------+----------------------------------------------------+

        +----------------+----------------------------------------------------+
        | Removed        | * :func:`wiz.graph.updated_by_distance`            |
        |                | * :func:`wiz.graph.extract_conflicting_nodes`      |
        +----------------+----------------------------------------------------+
        | Logic moved to | * :meth:`wiz.graph.Combination.resolve_conflicts`  |
        +----------------+----------------------------------------------------+

        +----------------+----------------------------------------------------+
        | Removed        | * :func:`wiz.graph.validate`                       |
        +----------------+----------------------------------------------------+
        | Logic moved to | * :meth:`wiz.graph.Combination.validate`           |
        +----------------+----------------------------------------------------+

        +----------------+----------------------------------------------------+
        | Removed        | * :func:`wiz.graph.extract_ordered_packages`       |
        +----------------+----------------------------------------------------+
        | Logic moved to | * :meth:`wiz.graph.Combination.extract_packages`   |
        +----------------+----------------------------------------------------+

    .. change:: changed

        Removed :func:`wiz.graph.relink_parents` and added logic to
        :meth:`wiz.graph.Graph.relink_parents`. This change was necessary to
        record potential relinking error within the graph instead of raising
        an exception immediately as the node bearing the error might be removed
        during the conflict resolution process.

    .. change:: new

        Added :func:`wiz.graph.generate_variant_permutations` to yield all
        possible permutations between variant groups in an optimized order.
        It now checks the requirement compatibility between each variant node to
        prevent wasting time in combinations that can not be resolved, hence
        providing a major performance boost for definition containing a lot of
        :ref:`variants <definition/variants>`.

    .. change:: new

        Added :func:`wiz.graph.compute_conflicting_matrix` to compute
        compatibility between each variant node.

    .. change:: changed

        Moved :func:`wiz.graph.sanitize_requirement` to
        :func:`wiz.utility.sanitize_requirement` and improved logic to prevent
        confusion when the package does not contain a :ref:`namespace
        <definition/namespace>`.

    .. change:: new

        Added :func:`wiz.utility.match` to check whether a
        :class:`~packaging.requirements.Requirement` instance is compatible
        with a :class:`wiz.package.Package` instance. This logic was previously
        included in :meth:`wiz.graph.Graph.find`.

    .. change:: new

        Added :func:`wiz.utility.extract_namespace` to retrieve a
        :ref:`namespace <definition/namespace>` from a
        :class:`~packaging.requirements.Requirement` instance. This logic was
        previously included in :meth:`wiz.graph.Graph.find`.

    .. change:: new

        Added :func:`wiz.utility.check_conflicting_requirements` to check
        whether two :class:`wiz.package.Package` instances contain conflicting
        requirements.

    .. change:: fixed

        Updated :class:`wiz.graph.Resolver` to prevent discarding graph
        combinations containing a node which has been flagged as conflict or
        error in a previous iteration. This logic was flawed as these nodes
        could be removed during the conflict resolution process, leading to a
        false negative evaluation of a graph combination.

    .. change:: fixed

        Updated :meth:`wiz.graph.Combination.resolve_conflicts` to better
        handle resolution of circular conflicts.

    .. change:: fixed

        Updated :meth:`wiz.graph.Resolver.discover_combinations` to prune
        unreachable nodes from the graph after downgrading node versions.
        Previously, variant conflicts could be detected from nodes which had
        been removed from the graph.

    .. change:: changed

        Updated following exception names for consistency:

        * :exc:`wiz.exception.InvalidVersion` →
          :exc:`wiz.exception.VersionError`
        * :exc:`wiz.exception.InvalidRequirement` →
          :exc:`wiz.exception.RequirementError`
        * :exc:`wiz.exception.IncorrectSystem` →
          :exc:`wiz.exception.CurrentSystemError`
        * :exc:`wiz.exception.IncorrectDefinition` →
          :exc:`wiz.exception.DefinitionError`

    .. change:: new

        Added new exceptions inheriting from
        :exc:`wiz.exception.GraphResolutionError` to better handle flow of data:

        * :exc:`wiz.exception.GraphConflictsError`
        * :exc:`wiz.exception.GraphInvalidNodesError`
        * :exc:`wiz.exception.GraphVariantsError`

    .. change:: changed

        Updated :class:`wiz.package.Package` constructor to raise an error if
        the variant index is missing or incorrect.

    .. change:: fixed

        Updated `monkey patching <https://en.wikipedia.org/wiki/Monkey_patch>`_
        of :class:`packaging.requirements.Requirement` to allow for multiple
        :ref:`namespaces <definition/namespace>` separated by two colons
        (e.g. ``name1::name2::foo``).

.. release:: 3.2.5
    :date: 2020-09-15

    .. change:: fixed

        Fixed :meth:`wiz.graph.Graph.find` to prevent returning nodes with
        a variant identifier not matching the
        :attr:`~packaging.requirements.Requirement.extras` attribute of the
        incoming requirement.

    .. change:: fixed

        Updated :class:`wiz.graph.Resolver` to raise a more palatable exception
        message when graph combination cannot be resolved because packages from
        a single variant group have requirement conflicts.

    .. change:: new

        Added :meth:`wiz.graph.Graph.variant_identifiers` to return all variant
        identifiers from the same definition identifier within the graph.

.. release:: 3.2.4
    :date: 2020-09-12

    .. change:: new

        Added link to `Google Group discussion page
        <https://groups.google.com/g/wiz-framework>`_.

.. release:: 3.2.3
    :date: 2020-09-11

    .. change:: fixed

        Updated :func:`wiz.command_line.display_definition` to display
        definition path and registry path when using ``wiz view`` command.

    .. change:: fixed

        Updated :mod:`wiz.history` to include definition path and registry
        path to history dump when serializing instances of
        :class:`~wiz.definition.Definition`.

.. release:: 3.2.2
    :date: 2020-09-09

    .. change:: fixed

        Updated :meth:`wiz.definition.Definition.ordered_data` to sort all dictionaries
        as :class:`collections.OrderedDict` instances in order to get consistent
        results.

.. release:: 3.2.1
    :date: 2020-09-08

    .. change:: fixed

        Updated :func:`wiz.utility.compute_file_name` to prevent including colons in the
        file name if the definition contains multiple namespaces (e.g. "foo::bar").
        Namespace separator symbols (``::``) are now replaced by hyphens.

.. release:: 3.2.0
    :date: 2020-09-03

    .. change:: changed

        Updated repository to use `versup
        <https://versup.readthedocs.io/en/latest/>`_ the help with the release
        process.

.. release:: 3.1.2
    :date: 2020-08-27

    .. change:: fixed

        Updated :func:`wiz.command_line._display_environ_from_context` to
        stringify truncated :envvar:`WIZ_CONTEXT` value in order to prevent
        error when displaying environment variables.

.. release:: 3.1.1
    :date: 2020-08-27

    .. change:: fixed

        Updated :func:`wiz.spawn.shell` to encode strings into "utf-8" before
        writing into the temporary file used for shell aliases. Previously, it
        would raise an error on Python 3.7 as
        :func:`tempfile.NamedTemporaryFile` only accept byte-like objects.

        .. seealso:: https://bugs.python.org/issue29245

.. release:: 3.1.0
    :date: 2020-08-26

    .. change:: changed
        :tags: command-line

        Renamed ``wiz install --registry`` to :option:`wiz install --output` to
        better differentiate the command from :option:`wiz --registry`.

    .. change:: new
        :tags: command-line

        Added short option ``-f`` to overwrite output when installing
        definitions and when editing a definition:

        * :option:`wiz install -f` for :option:`wiz install --overwrite`
        * :option:`wiz edit -f` for :option:`wiz edit --overwrite`

    .. change:: changed
        :tags: command-line

        Renamed ``wiz freeze -f/--format`` to :option:`wiz freeze -F/--format
        <wiz freeze -F>` to prevent confusion as the short option ``-f`` is used
        for overwriting outputs.

    .. change:: changed
        :tags: command-line

        Removed the ``wiz analyze -f/--filter`` options and make it into a
        non-required positional option instead to prevent confusion as the short
        option ``-f`` is used for overwriting outputs.

        .. extended-code-block:: bash
            :icon: ../image/avoid.png

            # Analyze all definitions whose identifiers matched "foo" or "bar"
            >>> wiz analyze -f "foo" -f "bar"

        .. extended-code-block:: bash
            :icon: ../image/prefer.png

            # Analyze all definitions whose identifiers matched "foo" or "bar"
            >>> wiz analyze "foo" "bar"

    .. change:: changed

        Updated the following modules to add compatibility with python 3.7 and
        3.8:

        * :mod:`wiz.command_line`
        * :mod:`wiz.filesystem`
        * :mod:`wiz.package`
        * :mod:`wiz.system`
        * :mod:`wiz.utility`

    .. change:: changed

        Updated :mod:`wiz.validator` to use custom definition validation instead
        of the `jsonschema <https://pypi.org/project/jsonschema/>`_ library
        which is based on `JSON Schema <https://json-schema.org/>`_ validation
        as it was hindering the performance when creating an instance of
        :class:`wiz.definition.Definition`.

        Removed :func:`wiz.validator.yield_definition_errors` and added
        :func:`wiz.validator.validate_definition` to perform equivalent
        tests in shorter time.

        Here is a benchmark with average speed when loading a definition:

        ==================================  ==========  =================
        Examples                            jsonschema  custom validation
        ==================================  ==========  =================
        minimal definition                  ~199us      ~63us
        simple definition                   ~2ms        ~1.6ms
        complex definition                  ~4.2s       ~3.3s
        ==================================  ==========  =================

        *(A complex definition contains 100 variants, 100 requirements and
        100 environment variables.)*

    .. change:: changed

        Updated :class:`wiz.definition.Definition` construction to use
        :func:`wiz.validator.validate_definition`.

    .. change:: changed

        Updated code to use `ujson <https://pypi.org/project/ujson/>`_ instead
        of the built-in :mod:`json` module to optimize the loading of
        :term:`JSON` files.

    .. change:: changed

        Updated :class:`wiz.definition.Definition` construction to provide an
        option to prevent using :func:`copy.deepcopy` on input data mapping to
        speed up instantiation whenever necessary::

            >>> Definition({"identifier": "foo"}, copy_data=False)

        By default, "copy_data" is set to True as it can cause unexpected issues
        when input data is being mutated::

            >>> data = {"identifier": "foo"}
            >>> definition = wiz.definition.Definition(data, copy_data=False)
            >>> print(definition.identifier)
            "foo"

            >>> del data["identifier"]
            >>> print(definition.identifier)
            KeyError: 'identifier'

    .. change:: changed

        Updated :func:`wiz.definition.load` to not copy input data mapping as it
        hindered performance.

        Here is a benchmark with average speed when loading a definition:

        ==================================  ==========  =============
        Examples                            with copy    without copy
        ==================================  ==========  =============
        minimal definition                  ~199us      ~177us
        simple definition                   ~2ms        ~1.8ms
        complex definition                  ~4.2s       ~2.7s
        ==================================  ==========  =============

        *(A complex definition contains 100 variants, 100 requirements and
        100 environment variables.)*

    .. change:: changed

        Updated :class:`wiz.definition.Definition` and
        :class:`wiz.package.Package` constructions to not perform the following
        conversions as it hindered performance:

        * Convert :ref:`definition/version` value into
          :class:`~packaging.version.Version` instance.
        * Convert :ref:`definition/requirements` and
          :ref:`definition/conditions` values into
          :class:`~packaging.requirements.Requirement` instances.
        * Convert :ref:`definition/requirements` and
          :ref:`definition/conditions` values within :ref:`definition/variants`
          into :class:`~packaging.requirements.Requirement` instances.

        Instead, these attributes will be converted and cached the first time
        they are accessed.

        Here is a benchmark with average speed when loading a definition:

        ==================================  ===============  ==================
        Examples                            with conversion  without conversion
        ==================================  ===============  ==================
        minimal definition                  ~199us           ~180us
        simple definition                   ~2ms             ~300us
        complex definition                  ~4.2s            ~156ms
        ==================================  ===============  ==================

        *(A complex definition contains 100 variants, 100 requirements and
        100 environment variables.)*

    .. change:: changed

        Updated :class:`wiz.definition.Definition` construction to simplify
        logic. It does not inherit from :class:`collections.Mapping` anymore and
        does not require from registry and definition location to be included in
        the mapping.

        .. extended-code-block:: python
            :icon: ../image/avoid.png

            >>> Definition({
            ...    "identifier": "foo",
            ...    "definition-location": "/path/to/definition.json",
            ...    "registry": "/path/to/registry",
            ... })

        .. extended-code-block:: python
            :icon: ../image/prefer.png

            >>> Definition(
            ...     {"identifier": "foo"},
            ...     path="/path/to/definition.json",
            ...     registry_path="/path/to/registry",
            ... )

        This prevents having to sanitize the definition data before exporting.

    .. change:: changed

        Removed :meth:`wiz.definition.Definition.sanitized` which was previously
        used to remove the "registry" and "definition-location" keywords from
        data definition as it is not necessary anymore.

    .. change:: changed

        Updated :class:`wiz.package.Package` construction to simplify logic
        and optimize performance. It does not inherit from
        :class:`collections.Mapping` anymore and uses
        :class:`wiz.definition.Definition` keywords instead of copying data.

        Instance of :class:`wiz.package.Package` can not mutate its content
        anymore.

    .. change:: changed

        Removed :mod:`wiz.mapping` as logic has been moved into
        :class:`wiz.definition.Definition`.

    .. change:: changed

        Updated :meth:`wiz.package.Package.identifier` to prepend
        :ref:`definition/namespace` to ensure that a unique identifier is always
        used. As a result, :meth:`wiz.package.Package.qualified_identifier`
        has been removed.

    .. change:: changed

        Updated :meth:`wiz.graph.Graph.update_from_requirements` to raise a
        palatable error when a dependent definition uses an invalid requirement
        as :ref:`definition/requirements` or :ref:`definition/conditions`
        attributes.

        Previously, these attributes were sanitized when instantiating the
        :class:`wiz.definition.Definition`.

    .. change:: fixed

        Fixed :class:`wiz.graph.Resolver` to ensure that conflicted nodes are
        always sorted in ascending order of distance from the :attr:`root
        <wiz.graph.Graph.ROOT>` level of the graph.

        Previously, conflicting nodes would not be sorted properly when new
        packages are added to the graph during the conflict resolution process,
        resulting in potentially unresolvable conflicts of packages that should
        have been removed before.

    .. change:: fixed

        Fixed :func:`wiz.utility.extract_version_ranges` to sort specifiers
        properly for deterministic results.

        Previously, it would sometimes fail to update minimal and maximum
        versions of the range in particular conditions.

    .. change:: changed

        Updated :func:`wiz.utility.compute_file_name` to prepend the
        :ref:`definition/namespace` value when creating a :term:`JSON` file name
        from an instance of :class:`wiz.definition.Definition`. Previously, name
        clashes were possible when exporting two definitions with the same
        :ref:`definition/identifier`, :ref:`definition/version` and
        :ref:`System Constraint <definition/system>` into the same registry.

    .. change:: changed

        Renamed following functions to use American spelling for consistency:

        * :func:`wiz.environ.sanitise` → :func:`wiz.environ.sanitize`
        * :func:`wiz.filesystem.sanitise_value` →
          :func:`wiz.filesystem.sanitize_value`

    .. change:: changed

        Updated all docstrings to use `Sphinx format
        <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format>`_.

.. release:: 3.0.0
    :date: 2020-08-05

    .. change:: changed

        Project name has been changed to ``wiz-env`` to guarantee a unique name
        on `Pypi <https://pypi.org/>`_.

    .. change:: new

        Added :mod:`wiz.config` to handle :term:`TOML` configuration and
        plugins to customize Wiz default values and callbacks.

        .. seealso::

            * :ref:`configuration`
            * :ref:`plugins`

    .. change:: new

        Added default plugin to register installation callback to deploy
        package definitions to a registry path.

        .. seealso:: :ref:`plugins/default/installer`

    .. change:: new

        Added default plugin to initialize environment variables.

        .. seealso:: :ref:`plugins/default/environ`

    .. change:: changed

        Removed :func:`wiz.install_definitions` and
        :func:`wiz.registry.install_to_vcs` as the concept of Local and VCS
        registry has been removed.

        Default plugin only install package definition to a registry path.

        .. seealso:: :ref:`plugins/default/installer`

        Custom plugin can be used to extend the installation logic.

    .. change:: changed

        Updated :ref:`command_line` to use configuration mapping to initialize
        default values.

    .. change:: changed

        Updated :func:`wiz.registry.get_defaults` to return registry paths from
        the configuration mapping instead of using a hardcoded list of paths.

        .. seealso:: :ref:`configuration/registry_paths`

    .. change:: changed

        Updated :func:`wiz.environ.initiate` to set initial environment
        variables from configuration mapping instead of using a hardcoded
        mapping.

        .. seealso:: :ref:`configuration/initial_environment`

    .. change:: new

        Added :func:`wiz.utility.deep_update` to merge two mappings recursively.

    .. change:: changed

        Updated documentation to remove Mill Specific examples.

.. release:: 2.6.5
    :date: 2019-04-04

    .. change:: fixed

        Updated the GitLab links to their fully qualified domain name,
        as the `resolv.conf <https://en.wikipedia.org/wiki/Resolv.conf>`_ setup
        is not consistent globally, which leads to it currently not resolving in
        all Mill sites.

    .. change:: fixed
        :tags: resolver

        Updated :meth:`wiz.graph.Graph.variant_groups` to preserve the order
        of variants defined in the definition. Previously it would sort the
        variant by version and by name.

.. release:: 2.6.4
    :date: 2019-04-02

    .. change:: fixed
        :tags: command-line

        Updated ``wiz search`` to use the qualified definition identifier when
        registering the commands. Otherwise, it wouldn't find the definition
        corresponding to a particular command.

.. release:: 2.6.3
    :date: 2019-03-29

    .. change:: fixed
        :tags: API

        Updated :func:`wiz.resolve_context` to use qualified identifiers when
        creating the :envvar:`WIZ_CONTEXT` environment variable which contains
        the :func:`encoded <wiz.utility.encode>` list of package identifiers.
        Previously, it would sometimes be impossible to retrieve a package from
        identifier in this list when the :ref:`namespace <definition/namespace>`
        is not specified.

.. release:: 2.6.2
    :date: 2019-03-29

    .. change:: fixed
        :tags: API

        Removed :class:`wiz.graph.Timeout` and updated
        :func:`wiz.resolve_context`, :func:`wiz.validate_definition` and
        :class:`wiz.graph.Resolver` to remove the "timeout" keyword argument.

        The timeout logic uses :mod:`signal` which can only be used in the main
        thread, therefore it was impossible to use Wiz within threads.

.. release:: 2.6.1
    :date: 2019-03-28

    .. change:: fixed
        :tags: documentation

        Fixed error in ``tutorial``.

.. release:: 2.6.0
    :date: 2019-03-28

    .. change:: changed
        :tags: documentation

        Updated ``tutorial``.

    .. change:: changed
        :tags: command-line

        Updated ``wiz list command`` to display the corresponding system
        requirement only if :option:`wiz list command --no-arch` is used.

    .. change:: changed
        :tags: command-line

        Updated ``wiz list package`` to display the corresponding system
        requirement only if :option:`wiz list package --no-arch` is used.

    .. change:: fixed
        :tags: command-line, API

        Updated :func:`wiz.definition.fetch` and ``wiz list command`` to use
        the qualified definition identifier when registering the commands.
        Otherwise, it wouldn't find the definition corresponding to a particular
        command.

.. release:: 2.5.0
    :date: 2019-03-27

    .. change:: changed
        :tags: debug

        Updated :func:`wiz.history.start_recording` to add a "minimal_actions"
        option which only keeps the 'identifier' keyword from each action
        recorded and discards all other elements passed to
        :func:`wiz.history.record_action`.

        This option is used to preserve the accuracy of execution time in
        the :option:`wiz analyze --verbose` command line option.

    .. change:: fixed
        :tags: debug

        Updated :func:`wiz.history.record_action` to copy each action in order
        to prevent mutating its content.

.. release:: 2.4.0
    :date: 2019-03-26

    .. change:: changed
        :tags: command-line

        Explicitly set the name of the program to "wiz" instead of relying on
        :data:`sys.argv` in order to prevent "__main__.py" to be displayed when
        the command is being run as follows::

            python -m wiz --help

.. release:: 2.3.0
    :date: 2019-03-20

    .. change:: new
        :tags: command-line

        Added :option:`wiz analyze --verbose` to print out information about
        history and execution time for each definition.

    .. change:: new
        :tags: command-line

        Added `wiz analyze --filter` to only display targeted definitions. The
        :attr:`qualified version identifier
        <wiz.definition.Definition.qualified_version_identifier>` should match
        all filters for each definition displayed.

    .. change:: new
        :tags: API

        Added :meth:`wiz.logging.Logger.debug_traceback` to log traceback from
        latest error raised as a debug message.

    .. change:: changed
        :tags: debug

        Updated :func:`wiz.history.start_recording` to reset global history.
        Previously, part of the global history mapping would be kept when the
        recording was started several times.

    .. change:: changed
        :tags: debug

        Updated :func:`wiz.history.record_action` to prevent it from serializing
        all actions as it affects the execution time tremendously.

    .. change:: changed
        :tags: command-line

        Updated to always log tracebacks as debug messages in order to reduce
        verbosity for command line usage in non-debug verbosity level.

    .. change:: fixed

        Updated :func:`wiz.registry.install_to_vcs` to
        :meth:`sanitize <wiz.definition.Definition.sanitized>` definitions before
        installation.

.. release:: 2.2.0
    :date: 2019-03-14

    .. change:: new
        :tags: command-line

        Added ``wiz analyze`` sub-command to check the validity of accessible
        definitions from registries.

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.colored_text` to return a text with a specific
        terminal color.

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.extract_version_ranges` to extract the minimum
        and maximum version from a :class:`packaging.requirements.Requirement`
        instance.

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.is_overlapping` to indicate whether two
        :class:`packaging.requirements.Requirement` instances are overlapping.
        It will be used to identify the nodes with conflicting requirements
        within during the graph resolution process.

    .. change:: new
        :tags: API

        Added :func:`wiz.validate_definition` to return a validation mapping of
        a definition with possible errors and warnings.

    .. change:: changed
        :tags: command-line, API

        Removed ``mlog`` dependency and added :mod:`wiz.logging` using
        :mod:`sawmill` directly to have more flexibility to configure the
        :class:`wiz.logging.Logger` instance.

        :func:`wiz.logging.configure_for_debug` has then be added in order to
        record logs instead of displaying it directly to the user. It was
        necessary to ensure a clear formatting for the ``wiz analyze``
        sub-command.

    .. change:: changed
        :tags: API

        Updated :func:`wiz.utility.compute_label` to retrieve qualified
        identifier of input definition.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.graph.remove_node_and_relink` to
        :func:`wiz.graph.relink_parents` as the node removal process is
        extracted out of the function.

        During the conflict resolution process, sometimes an extra step is
        needed that adds additional packages to the graph. This ensures that the
        matching nodes exist in the graph when the parents of the conflicting
        nodes are relinked.

        Furthermore, the matching nodes are now fetched via the
        :meth:`wiz.Graph.find` method instead of passing a list of package
        identifiers to the function to simplify the function's logic.

        Finally, an error is raised when a node's parent cannot be linked to any
        other node to ensure that their requirements are always fulfilled.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.graph.extract_parents` to
        :func:`wiz.graph.extract_conflicting_requirements` to return a list
        of requirement conflict mappings from a list of nodes instead of simply
        returning the list of parent identifiers.

        :func:`wiz.utility.is_overlapping` is used to identify the parent with
        conflicting requirements.

    .. change:: changed
        :tags: API

        Updated :exc:`wiz.exception.GraphResolutionError` to record a
        requirement conflict mapping in a `conflicts` attribute if necessary. It
        will be used to record requirement conflicts from failed combinations in
        the :class:`wiz.graph.Resolver` instance.

    .. change:: changed

        Updated :class:`wiz.graph.Resolver` to better keep track of node errors
        and requirement conflicts to prevent any graph combination to be
        generated when at least one node error or conflict is detected.

        It uses the `conflicts` attribute added to the
        :exc:`wiz.exception.GraphResolutionError` exception.

    .. change:: changed

        Updated :class:`wiz.graph.Resolver` to add an additional step once all
        graph combinations from the initial requirements have failed to resolve.
        This step attempts to replace the nodes with conflicting requirements
        by compatible versions which could lead to a resolution.

        It uses the `conflicts` attribute added to the
        :exc:`wiz.exception.GraphResolutionError` exception.

    .. change:: fixed

        Updated :class:`wiz.graph.Resolver` and :class:`wiz.graph.Graph` to
        ensure that packages added during the conflict resolution process are
        correctly linked to the parent nodes instead of
        :attr:`root <wiz.graph.Graph.ROOT>`.

    .. change:: fixed

        Updated :class:`wiz.graph.Resolver` and :class:`wiz.graph.Graph` to
        ensure that node requirements are always fulfilled when computing a
        graph with one particular :func:`combination
        <wiz.graph.generate_variant_combinations>`. Previously, nodes removed
        during the graph combination process were not properly reconnected to
        other node(s) in the graph.

    .. change:: fixed
        :tags: API

        Updated :func:`wiz.definition.query` to take an extra parameter from a
        :class:`packaging.requirements.Requirement` instance into account when
        querying a definition with a specific variant (e.g. "foo[Variant]"). If
        the best matching definition version does not contain the required
        variant, older versions would be fetched until one that contains the
        required variant will be returned.

.. release:: 2.1.0
    :date: 2019-02-11

    .. change:: changed

        Updated :func:`wiz.definition.query` to add the following rule when
        guessing the namespace of a package definition: If several namespaces
        are available, default to the one which is identical to the identifier
        if possible.

        For instance, the following command will default to ``massive::massive``
        even if ``maya::massive`` is available::

            >> wiz use massive

.. release:: 2.0.0
    :date: 2019-02-04

    .. change:: new
        :tags: command-line

        Added :option:`--add-registry <wiz --add-registry>` to specify a path to
        be added to the default registry paths. Previously it was only possible
        to replace the default paths with :option:`--definition-search-paths
        <wiz --registry>`.

    .. change:: new
        :tags: command-line

        Added ``--timeout`` to specify a time limit after
        which a graph resolve should be aborted to avoid the process hanging.

    .. change:: new
        :tags: command-line

        Added :option:`--init <wiz --init>` to specify initial environment
        variables, which will be extended by the resolved environment.
        For example, now it is possible to hand in a PATH or PYTHONPATH, without
        making them available in a definition.

    .. change:: new
        :tags: command-line

        Added :option:`--version <wiz --version>` to display the package
        version.

    .. change:: new
        :tags: command-line

        Added ``wiz edit`` sub-command to edit one or several definitions with
        the default editor or with operation option(s).

    .. change:: new
        :tags: command-line

        Updated ``wiz run`` sub-command to accept unknown arguments and
        automatically consider it as an extra argument which will be appended to
        the command.

        For instance, both of the following commands are valid::

            >>> wiz run python -- -c 'print("TEST")'
            >>> wiz run python -c 'print("TEST")'

    .. change:: new
        :tags: command-line

        Added :option:`wiz search --no-arch`,
        :option:`wiz list command --no-arch` and
        :option:`wiz list package --no-arch` options to display all definitions
        discovered, even when not compatible with the current system.

    .. change:: new
        :tags: definition, backwards-incompatible

        Added optional :ref:`conditions <definition/conditions>` keyword to
        definition schema which can be used to indicate a list of packages
        which must be in the resolution graph for the package to be included.

    .. change:: new
        :tags: definition, backwards-incompatible

        Added optional :ref:`namespace <definition/namespace>` keyword which
        can be used to provide a scope to a definition. It replaces the
        "group" keyword as it is also used to define where in the hierarchy of a
        VCS Registry a definition will be installed.

    .. change:: new
        :tags: definition

        Added optional :ref:`install-root <definition/install_root>`
        keyword to definition schema to indicate the root of the install
        location of a package. The value set for this keyword can be referenced
        in the definition with :envvar:`INSTALL_ROOT` and should form the base
        of the :ref:`install-location <definition/install_location>` value.

    .. change:: new
        :tags: API

        Added :mod:`wiz.environ` module to regroup functions dealing with the
        environment mapping resolution. Added :mod:`wiz.environ.contains` to
        identify specific environment variable in string and
        :mod:`wiz.environ.substitute` to replace environment variables by their
        respective values in string.

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.combine_command` to return command elements
        as a unified command string while keeping quoted elements in order
        to preserve the command in the log as it was typed.

    .. change:: new
        :tags: API

        Added :func:`wiz.graph.validate` to ensure that a :class:`Graph`
        instance does not contain any remaining error after the conflict
        resolution process. The :exc:`wiz.exception.WizError` error encapsulated
        in the nearest accessible node will be raised if necessary.

    .. change:: changed
        :tags: definition

        Removed the ``constraints`` keyword to simplify the graph resolution as
        :ref:`conditions <definition/conditions>` could be used instead to reach
        the same logic.

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

    .. change:: changed
        :tags: shell

        Updated :func:`wiz.spawn.shell` to add "command" aliases to subprocess
        when a Wiz shell is being opened, thereby enabling the user to use the
        same aliases in the sub-shell that have been defined in the definitions.

    .. change:: changed
        :tags: shell, backwards-incompatible

        Updated :func:`wiz.spawn.shell`  to limit the Wiz shell to "bash".

    .. change:: changed
        :tags: command-line

        Updated :mod:`wiz.command_line` to use :mod:`click` instead of
        :mod:`argparse` in order to improve code maintainability.

    .. change:: new
        :tags: command-line

        Renamed :option:`--definition-search-paths <wiz --registry>` to
        :option:`--registry <wiz --registry>` for clarity.

    .. change:: new
        :tags: command-line

        Renamed :option:`--definition-search-depth <wiz --registry-depth>` to
        :option:`--registry-depth <wiz --registry-depth>` for clarity.

    .. change:: changed
        :tags: command-line, backwards-incompatible

        Updated command line arguments to use the same option
        ``--registry`` for installing to a Local Registry and installing to a
        VCS Registry. Previously the argument was split into `--registry-path`
        and `--registry-id`.

        Now definitions can be installed using the following commands syntax::

            # For local registries
            >>> wiz install foo.json --registry /path/to/registry
            >>> wiz install foo.json -r /path/to/registry

            # For VCS registries
            >>> wiz install foo.json -registry wiz://primary-registry
            >>> wiz install foo.json -r wiz://primary-registry

    .. change:: changed
        :tags: command-line

        Updated ``wiz search`` sub-command to also search packages using
        command aliases.

    .. change:: changed
        :tags: command-line

        Updated sub-commands to only accept extra arguments for the ``wiz use``
        and ``wiz run`` sub-commands in order to execute a custom command
        within a resolved context. Previously, extra arguments were accepted by
        all sub-commands, which is not desired.

        For instance, extra arguments could be used as follow::

            wiz use python -- python -c 'print("TEST")'
            wiz run python -- -c 'print("TEST")'

    .. change:: changed
        :tags: API, backwards-incompatible

        Updated :func:`wiz.resolve_context` to prepend implicit requests to
        explicit requests, rather than append as it previously did.

        Previously when resolving the environment, a path set in the 'environ'
        of an implicit package would be appended to the ones from explicit
        packages, making it impossible to overwrite (e.g. shader paths from
        within implicit packages).

        This change enables the use of implicit packages for job setups by
        guaranteeing that implicit packages will be resolved before explicit
        packages.

    .. change:: changed
        :tags: API, command-line

        Updated :func:`wiz.spawn.execute` to substitute environment variables
        within command elements before the execution process. User can then
        use environment variables in command, such as::

            >>> wiz use python -- echo \$PIP_CONFIG_FILE

    .. change:: changed
        :tags: API, command-line, backwards-incompatible

        Updated :func:`wiz.definition.fetch` to remove "requests" option which
        could filter definitions discovered. The filtering process has been
        moved to the command line in order to filter definitions from all
        systems as the definition mapping returned by
        :func:`wiz.definition.fetch` only records one definition per identifier
        and version.

    .. change:: changed
        :tags: API, command-line, backwards-incompatible

        Removed `--install-location` option from ``wiz install`` sub-command
        and "install_location" argument from :func:`wiz.install_definitions` as
        this can already be set with the ``wiz edit`` command before installing,
        and just adds redundant complexity.

    .. change:: changed
        :tags: API

        Updated :func:`wiz.spawn.execute` to display a nicer error handling for
        the shell, when a command can not be found or executed. Now, when an
        :exc:`OSError` is detected, it will throw an error message instead of a
        traceback (A traceback is available if verbosity is set to 'debug').

    .. change:: changed
        :tags: API

        Updated :func:`wiz.definition.discover` to add a "system_mapping" option
        which can filter out definitions :func:`invalid <wiz.system.validate>`
        with a system mapping.

    .. change:: changed
        :tags: API, backwards-incompatible

        Moved :func:`wiz.package.initiate_environ` to
        :func:`wiz.environ.initiate`.

    .. change:: changed
        :tags: API, backwards-incompatible

        Moved :func:`wiz.package.sanitise_environ_mapping` to
        :func:`wiz.environ.sanitise`.

    .. change:: changed
        :tags: API

        Updated :mod:`wiz.resolve_command` to return resolved list of elements
        composing the command from elements composing input command. It prevents
        unnecessary combination which could affect the nature of the command by
        removing single and double quotes.

    .. change:: changed
        :tags: API

        Updated :func:`wiz.package.initiate_environ` to add the
        :envvar:`HOSTNAME` environment variable into the initial environment.

    .. change:: changed
        :tags: API

        Updated :func:`wiz.definition.export` to sanitized the definition with
        :meth:`wiz.definition.Definition.sanitized` before exporting it.

    .. change:: changed
        :tags: API

        Updated :func:`wiz.definition.load` to add 'definition-location' keyword
        in mapping. Previously this would only be added by
        :func:`wiz.definition.discover`.

    .. change:: changed
        :tags: API, backwards-incompatible

        Added :func:`wiz.package.create` to instantiate a
        :class:`~wiz.package.Package` instance from a
        :class:`~wiz.definition.Definition` instance and variant identifier,
        and updated :class:`~wiz.package.Package` constructor to just take a
        mapping. This modification ensure that edition methods will work with
        packages (e.g. :meth:`~wiz.mapping.Mapping.set`,
        :meth:`~wiz.mapping.Mapping.remove`,...).

    .. change:: changed
        :tags: API, backwards-incompatible

        Removed :func:`wiz.package.generate_identifier` and add
        :attr:`wiz.definition.Definition.version_identifier` property to get
        version identifiers from :class:`~wiz.definition.Definition` instance.

    .. change:: changed
        :tags: API

        Added the following properties to get qualified identifiers from
        :class:`~wiz.definition.Definition` and :class:`~wiz.package.Package`
        instances:

        * :attr:`wiz.definition.Definition.qualified_identifier`
        * :attr:`wiz.definition.Definition.qualified_version_identifier`
        * :attr:`wiz.package.Package.qualified_identifier`

    .. change:: changed
        :tags: API

        Updated :class:`wiz.graph.Resolver` and :class:`wiz.graph.Graph` to take
        conditions into account while resolving the graph.

    .. change:: changed
        :tags: API

        Updated :class:`wiz.graph.Resolver` and :class:`wiz.graph.Graph` to
        handle package extraction error so that it does not raise if faulty
        packages are not in resolved packages. If a package extraction error is
        raised for one combination of the graph, another graph combination will
        be fetched and the error will be raised only if it appears for all
        combinations.

        The package extraction error has now a lower priority, so that it will
        not be raised if a conflict error is raised before.

    .. change:: changed
        :tags: API

        Updated :meth:`graph.Graph.create_link` to not raise an error when a
        link is assigned twice between two nodes. This caused an issue when
        a package :ref:`implicitly required <definition/auto-use>` were also
        explicitly required. Instead, it now gives priority to the link with
        the lowest weight so it has the highest priority possible.

        .. note::

            If a package is required twice with two different requests, the
            first request only will be kept::

                # The following command will discard 'foo>2'
                wiz use foo foo>2

    .. change:: changed
        :tags: API

        Updated :class:`wiz.resolve_context` to add an optional "timeout"
        argument in order to modify the default graph resolution time limit.

    .. change:: fixed

        Fixed :func:`wiz.graph.combined_requirements` to take requirements from
        all parent nodes into account. Previously it would use the distance
        mapping, which would automatically pick the node with the shortest path
        as the only parent to consider for requirements. That lead to the
        elimination of all requirement from other parents, so conflicts would
        not be properly detected and resolved within the graph.

    .. change:: fixed

        Fixed :func:`wiz.graph.updated_by_distance` to not filter out
        :attr:`root <wiz.graph.Graph.ROOT>` node.

    .. change:: fixed

        Changed :mod:`wiz.validator` to open the definition `JSON Schema
        <https://json-schema.org/>`_ once the module is loaded, rather than once
        per validation. Previously a "too many files opened" issue could be
        encountered when creating multiple definitions in parallel.

    .. change:: fixed

        Fixed :func:`wiz.registry.fetch` to resolve the absolute path of the
        registry in order to prevent the fetching process to fail with relative
        paths or trailing slashes.

    .. change:: fixed

        Fixed :class:`wiz.mapping.Mapping` to ensure that creating an instance
        does not mutate original data.

    .. change:: fixed
        :tags: command-line, debug

        Fixed :option:`--record <wiz --record>` command to ensure that path
        exists before exporting history.

.. release:: 1.2.1
    :date: 2018-10-24

    .. change:: fixed

        Fixed :func:`wiz.spawn.execute` to use the :func:`subprocess.call`
        convenience function which is less likely to leave remaining
        sub-processed when the parent is killed.

        This was an issue as the render farm is using :data:`signal.SIGKILL`
        to interrupt a job.

.. release:: 1.2.0
    :date: 2018-10-24

    .. change:: new
        :tags: command-line

        Added ``wiz install`` sub-command to install package definition to a
        registry.

    .. change:: new
        :tags: definition

        Added optional :ref:`group <definition/namespace>` keyword to definition
        schema, which can be used to define where in the hierarchy of a
        VCS Registry a definition will be installed (e.g. "python",
        "maya").

    .. change:: new
        :tags: definition

        Added optional :ref:`install-location <definition/install_location>`
        keyword to definition schema to indicate the location of a package
        data.

    .. change:: new
        :tags: API

        Added :func:`wiz.install_definitions_to_path` and
        :func:`wiz.install_definitions_to_vcs` to install one or several
        definition files to a Local Registry or a VCS Registry.

    .. change:: new
        :tags: API

        Added :func:`wiz.registry.install_to_path` and
        :func:`wiz.registry.install_to_vcs` to install a definition instance
        to a Local Registry or a VCS Registry.

    .. change:: new
        :tags: API

        Added :meth:`wiz.package.Package.localized_environ` to return
        environment mapping of a package which replace the
        :envvar:`INSTALL_LOCATION` environment variable by the
        :ref:`install-location <definition/install_location>` keyword value.

    .. change:: new
        :tags: API

        Added :meth:`wiz.definition.Definition.sanitized` to return a definition
        without keywords implemented when the definition is :func:`discovered
        <wiz.definition.discover>`. Only the keywords unrelated to the registry
        are preserved so that sanitized definition can be compared and
        installed.

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.compute_label` to compute a unique label for
        a definition (e.g. "'foo' [0.1.0]").

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.compute_system_label` to compute a unique label
        for the :ref:`system <definition/system>` value of a definition (e.g.
        "linux : x86_64 : el >= 6, 7").

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.compute_file_name` to compute a unique
        :term:`JSON` file name for a definition (e.g. "foo-0.1.0.json").

    .. change:: new
        :tags: documentation

        Added :ref:`environment variable <environment_variables>` section to
        list and describe the environment variables used by Wiz.

    .. change:: new
        :tags: documentation

        Added :ref:`definition/install_location` to :ref:`definition` section.

    .. change:: changed
        :tags: definition

        Renamed keyword 'origin' to 'definition-location', to be more consistent
        with the newly added 'install-location' keyword.

    .. change:: fixed

        Actually return a copy in :func:`wiz.definition._Variant.copy`.

.. release:: 1.1.1
    :date: 2018-10-23

    .. change:: fixed
        :tags: API

        Fixed :class:`wiz.definition._Variant` to ensure that it can be
        initiated with "\*args" and "\*\*kwargs" like its mother class
        :class:`wiz.mapping.Mapping`. The manipulation methods would not work
        otherwise as it attempted to create a new Variant instance without the
        "definition_identifier" argument.

.. release:: 1.1.0
    :date: 2018-10-23

    .. change:: changed
        :tags: API

        Moved manipulation methods :meth:`~wiz.definition.Definition.set`,
        :meth:`~wiz.definition.Definition.update`,
        :meth:`~wiz.definition.Definition.extend`,
        :meth:`~wiz.definition.Definition.insert`,
        :meth:`~wiz.definition.Definition.remove`,
        :meth:`~wiz.definition.Definition.remove_key`,
        :meth:`~wiz.definition.Definition.remove_index` to mother class
        :class:`wiz.mapping.Mapping` to ensure that logic is available in
        :class:`wiz.definition._Variant` object.

.. release:: 1.0.2
    :date: 2018-10-18

    .. change:: fixed

        Updated :mod:`wiz.command_line` to convert version to a string when
        freezing the environment. Previously it would fail with a type error.

.. release:: 1.0.1
    :date: 2018-09-24

    .. change:: fixed
        :tags: debug

        Fixed :func:`wiz.graph.Resolver` to store the extracted graph in the
        history mapping instead of the original one when recording the graph
        combination extraction action (identified with
        :data:`~wiz.symbol.GRAPH_COMBINATION_EXTRACTION_ACTION`).

.. release:: 1.0.0
    :date: 2018-09-05

    .. change:: new
        :tags: API

        Added :func:`wiz.graph.generate_variant_combinations` to create a
        :term:`generator iterator` with all graph combinations from a list of
        conflicting variant groups. Implemented it within
        :class:`wiz.graph.Resolver` instance instead of dividing the graph with
        all possible combinations to optimize the resolution process.

    .. change:: new
        :tags: API

        Added :func:`wiz.graph.remove_node_and_relink` to remove a node from the
        graph and connect node's parents to other nodes with a new requirement.
        This logic was previously part of
        :meth:`wiz.graph.Resolver.resolve_conflicts`.

    .. change:: new
        :tags: API

        Added :func:`wiz.graph.extract_parents` to extract existing parent node
        identifiers from a node.

    .. change:: changed
        :tags: API

        Updated :class:`wiz.graph.Resolver` and :class:`wiz.graph.Graph` to
        better handle graph division from variant groups added to the graph.
        Previously variant groups were simply identified during the package
        extraction process so a single variant could appear in several groups,
        which led to unnecessary graph divisions. Variant groups are now
        organized per definition identifier and updated for each package added
        to the graph when necessary.

    .. change:: changed
        :tags: API

        Updated :class:`wiz.graph.Graph` to record the number of times a node
        variant has been added to the graph and sort each variant group
        following two criteria: First by the number of occurrences of each node
        identifier in the graph and second by the variant index defined in the
        package definition. This will ensure that a variant called multiple
        times will have priority over the others during the graph division.

    .. change:: changed
        :tags: API

        Updated :class:`wiz.graph.Resolver` to better identify compatibility
        between package requirements during the conflict resolution process.
        Previously conflicting packages were compared with each other's
        requirement to ensure that at least one of them were matching both
        requirements. For instance:

        .. code-block:: none

            - 'foo==0.5.0' is required by 'foo<1';
            - 'foo==1.0.0' is required by 'foo';
            - The version '0.5.0' is matching both requirements;
            - Requirements 'foo<1' and 'foo' are seen as compatible.

        However, this strategy could not recognize when two conflicting packages
        had compatible requirements even when neither package versions could
        match both requirements:

        .. code-block:: none

            - 'foo==0.5.0' is required by 'foo<1';
            - 'foo==1.0.0' is required by 'foo!=0.5.0';
            - Versions '0.5.0' and '1.0.0' cannot match both requirements;
            - Requirements 'foo<1' and 'foo!=0.5.0' are seen as incompatible.

        The new strategy chosen is to directly attempt to :func:`extract
        <wiz.package.extract>` packages from the combination of both
        requirements so that an error could be raised according to the result.
        As a consequence, the latest example would not fail if a version
        'foo==0.2.0' can be fetched.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.graph.compute_priority_mapping` to
        :func:`wiz.graph.compute_distance_mapping` to prevent confusion as a
        shortest path algorithm (Dijkstra's algorithm) is being used to define
        the "priorities" which are the shortest possible paths from nodes to the
        root of the graph.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.graph.sorted_from_priority` to
        :func:`wiz.graph.updated_by_distance` for clarity.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.graph.extract_conflicted_nodes` to
        :func:`wiz.graph.extract_conflicting_nodes` for clarity.

    .. change:: changed
        :tags: API

        Updated :class:`wiz.graph.Resolver` to keep track of updates in the
        graph during the conflict resolution process in order to compute a new
        distance mapping only when necessary.

    .. change:: changed
        :tags: API

        Removed :func:`wiz.graph.validate_requirements` as this functionality
        is not necessary anymore.

    .. change:: changed
        :tags: API

        Removed :func:`wiz.graph.extract_requirement` as this functionality
        is not necessary anymore.

    .. change:: changed
        :tags: API

        Removed :meth:`wiz.graph.Graph.copy` as this functionality
        is not necessary anymore.

    .. change:: fixed
        :tags: API

        Fixed :class:`wiz.graph.Resolver` to keep track of definition
        identifiers which led to graph divisions to prevent dividing several
        time the graph with the same package variants when graph is being
        updated during conflict resolution process.

.. release:: 0.17.0
    :date: 2018-08-28

    .. change:: changed
        :tags: API

        Updated :func:`wiz.package.initiate_environ` to forward the
        :envvar:`XAUTHORITY` environment variable into the initial environment
        as it is required by some applications.

.. release:: 0.16.0
    :date: 2018-08-16

    .. change:: changed
        :tags: API

        Updated :func:`wiz.resolve_context` to make the *definition_mapping*
        argument optional. If no definition mapping is provided, a sensible one
        will be fetched from default registries.

    .. change:: changed
        :tags: API

        Updated :meth:`~wiz.definition.Definition.remove` method to return
        :class:`~wiz.definition.Definition` instance without raising
        :exc:`KeyError` exception when element to remove does not exist.

    .. change:: changed
        :tags: API

        Updated :meth:`~wiz.definition.Definition.remove_key` method to return
        :class:`~wiz.definition.Definition` instance without raising
        :exc:`KeyError` exception when element to remove does not exist.

    .. change:: changed
        :tags: API

        Updated :meth:`~wiz.definition.Definition.remove_key` method to return
        copy of a :class:`~wiz.definition.Definition` instance without element
        mapping if the latest key is removed.

    .. change:: changed
        :tags: API

        Updated :meth:`~wiz.definition.Definition.remove_index` method to return
        :class:`~wiz.definition.Definition` instance without raising
        :exc:`KeyError` exception when index to remove does not exist.

    .. change:: changed
        :tags: API

        Updated :meth:`~wiz.definition.Definition.remove_index` method to return
        copy of a :class:`~wiz.definition.Definition` instance without element
        list if the latest item is removed.

    .. change:: fixed
        :tags: API

        Fixed :mod:`wiz.mapping` to prevent serialisation of boolean values as
        it causes validation errors when serialized mapping is used to create
        a new :class:`~wiz.definition.Definition` instance.

.. release:: 0.15.1
    :date: 2018-08-14

    .. change:: fixed
        :tags: API

        Fixed :func:`wiz.definition.fetch` to sort implicit packages in inverse
        order of discovery to ensure that the package from the latest registries
        have highest priority.

    .. change:: fixed
        :tags: API

        Fixed :meth:`wiz.mapping.Mapping.to_ordered_dict` to ensure that
        the :ref:`auto-use <definition/auto-use>` keyword is displayed at a
        logical position in the serialized definition and package instances.

.. release:: 0.15.0
    :date: 2018-08-14

    .. change:: new
        :tags: API

        Added :meth:`~wiz.definition.Definition.set` method to return copy
        of a :class:`~wiz.definition.Definition` instance with a new element.

    .. change:: new
        :tags: API

        Added :meth:`~wiz.definition.Definition.update` method to return copy
        of a :class:`~wiz.definition.Definition` instance with element mapping
        updated.

    .. change:: new
        :tags: API

        Added :meth:`~wiz.definition.Definition.extend` method to return copy
        of a :class:`~wiz.definition.Definition` instance with element list
        extended.

    .. change:: new
        :tags: API

        Added :meth:`~wiz.definition.Definition.insert` method to return copy
        of a :class:`~wiz.definition.Definition` instance with element added
        to list at specific index.

    .. change:: new
        :tags: API

        Added :meth:`~wiz.definition.Definition.remove` method to return copy
        of a :class:`~wiz.definition.Definition` instance without a specific
        element.

    .. change:: new
        :tags: API

        Added :meth:`~wiz.definition.Definition.remove_key` method to return
        copy of a :class:`~wiz.definition.Definition` instance without a
        specific key in element mapping.

    .. change:: new
        :tags: API

        Added :meth:`~wiz.definition.Definition.remove_index` method to return
        copy of a :class:`~wiz.definition.Definition` instance without a
        specific index in element list.

    .. change:: new
        :tags: API

        Added :func:`wiz.load_definition` to conveniently alias the
        :func:`wiz.definition.load` function.

    .. change:: changed
        :tags: API

        Updated :func:`wiz.export_definition` to export a :term:`JSON` file from
        a mapping or a :class:`~wiz.definition.Definition` instance.

.. release:: 0.14.0
    :date: 2018-08-10

    .. change:: new
        :tags: definition

        Added optional ``constraints`` keyword to definition schema which
        indicates a list of package requirements which should be used to resolve
        a context only if another package with the same definition identifier is
        required.

    .. change:: new
        :tags: definition

        Added optional :ref:`auto-use <definition/auto-use>` keyword to
        definition schema which indicates whether corresponding package should
        be used implicitly to resolve context. Default is False.

    .. change:: new
        :tags: command-line

        Added :option:`--ignore-implicit <wiz --ignore-implicit>` command line
        option to skip implicit packages.

    .. change:: new
        :tags: API

        Added :func:`wiz.package.generate_identifier` to generate corresponding
        package identifier from a definition.

    .. change:: changed
        :tags: API

        Updated :func:`wiz.definition.fetch` to detect implicit package
        identifiers and add it to the definition mapping returned.

    .. change:: changed
        :tags: API

        Updated :meth:`wiz.graph.Graph.update_from_requirements` to take
        constraint packages into account while resolving the graph.

    .. change:: fixed
        :tags: API

        Fixed :meth:`wiz.graph.extract_requirement` to retrieve requirement when
        the parent node is :attr:`wiz.graph.Graph.ROOT`.

.. release:: 0.13.0
    :date: 2018-07-26

    .. change:: changed
        :tags: registry

        Changed :func:`wiz.registry.get_defaults` to update the location of the
        site registry folder in order to prevent using the :file:`.common`
        hidden folder.

        :file:`/jobs/.common/wiz/registry/default` →
        :file:`/jobs/.wiz/registry/default`

    .. change:: changed
        :tags: registry

        Changed :func:`wiz.registry.discover` to update the location of the
        project registry sub-folder in order to prevent using the
        :file:`.common` hidden folder.

        :file:`[PREFIX_PROJECT]/.common/wiz/registry` →
        :file:`[PREFIX_PROJECT]/.wiz/registry`

.. release:: 0.12.0
    :date: 2018-06-08

    .. change:: changed
        :tags: registry

        Changed :func:`wiz.registry.get_defaults` to update the location of the
        site registry folder.

        :file:`/jobs/.common/wiz/registry` → :file:`/jobs/.common/wiz/registry/default`

.. release:: 0.11.1
    :date: 2018-06-06

    .. change:: fixed

        Changed the `MANIFEST template
        <https://docs.python.org/2/distutils/sourcedist.html#the-manifest-in-template>`_
        to release the package source with :term:`JSON` files.

.. release:: 0.11.0
    :date: 2018-06-06

    .. change:: new
        :tags: API

        Added :func:`wiz.validator.yield_definition_errors` to identify and
        yield potential errors in a definition data following `JSON Schema
        <https://json-schema.org/>`_.

    .. change:: changed
        :tags: API

        Changed :class:`wiz.definition.Definition` to validate data mapping on
        instantiation and raise potential error as
        :exc:`~wiz.exception.IncorrectDefinition`.

    .. change:: changed
        :tags: API

        Changed :func:`wiz.export_definition` to take a data mapping instead of
        individually requesting each keyword.

        The "packages" argument which were used to pass a list of
        :class:`~wiz.package.Package` instances to indicate the requirements
        list is no longer necessary as the requirements list could directly be
        passed to the data mapping. This implies that the user no longer need to
        fetch the corresponding packages prior to export a definition.

    .. change:: changed
        :tags: API

        The :func:`wiz.export_bash_wrapper` and :func:`wiz.export_csh_wrapper`
        functions have been removed and replaced by an :func:`wiz.export_script`
        function which simply take a "script_type" argument.

.. release:: 0.10.0
    :date: 2018-05-24

    .. change:: changed

        Changed :func:`wiz.registry.discover` to yield all registry folders
        available within the path folder hierarchy if under :file:`/jobs/ads`

    .. change:: changed

        Changed :func:`wiz.registry.get_defaults` to update the location of the
        site registry folder and global registry folders.

.. release:: 0.9.2
    :date: 2018-04-30

    .. change:: changed
        :tags: logging

        Changed :func:`wiz.package.combine_command_mapping` to display a debug
        message instead of a warning message when a command from a package
        definition is being overridden in another package definition. As
        commands are being overridden for basically every usage (e.g. to add
        plugins to an application), this created confusion for the user.

.. release:: 0.9.1
    :date: 2018-04-27

    .. change:: changed
        :tags: API

        Changed :func:`wiz.discover_context` to add the resolved environment and
        command mappings to the context mapping returned.

.. release:: 0.9.0
    :date: 2018-04-26

    .. change:: new
        :tags: API

        Added :func:`wiz.fetch_package` to return best matching package instance
        from a package request.

    .. change:: new
        :tags: API

        Added :func:`wiz.fetch_package_request_from_command` to fetch the
        package request corresponding to a command request.

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.get_version` to build
        :class:`packaging.version.Version` instances while raising a
        :exc:`~wiz.exception.WizError` exception in case of failure.

    .. change:: new
        :tags: API

        Added :func:`wiz.utility.get_requirement` to build
        :class:`packaging.requirements.Requirement` instances while raising a
        :exc:`~wiz.exception.WizError` exception in case of failure.

    .. change:: changed
        :tags: command-line

        Changed the ``wiz view`` sub-command to only display the full definition
        if the request is identified as a package definition. If the request is
        identified as a command, only the corresponding definition identifier is
        displayed.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.query_definition` to :func:`wiz.fetch_definition`
        for consistency.

        To prevent confusion, it now returns definition instance from a
        package definition request only, not from a command request.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.fetch_definitions` function to
        :func:`wiz.fetch_definition_mapping` for clarity.

        To keep track of the origin of the definitions fetched, the registry
        paths are now added as a "registries" keyword to the mapping returned.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.query_current_context` function to
        :func:`wiz.discover_context` for clarity.

        To prevent incorrect packages to be fetched from different registries,
        the original registry list is now stored in a :envvar:`WIZ_CONTEXT`
        environment variable along with the package identifiers so that a valid
        definition mapping could be fetched internally.

    .. change:: changed
        :tags: API

        Renamed :func:`wiz.resolve_package_context` function to
        :func:`wiz.resolve_context` for consistency.

        To prevent incorrect packages to be fetched from different registries
        when discovering the context from a resolved environment, the encoded
        package identifiers are now stored in a :envvar:`WIZ_CONTEXT`
        environment variable along with the registry list.

    .. change:: changed
        :tags: API

        Removed :func:`wiz.resolve_command_context` for consistency as the
        context should be only retrievable with a package request.

.. release:: 0.8.2
    :date: 2018-04-23

    .. change:: fixed
        :tags: API

        Added packages list to the context mapping retrieved by the
        :func:`wiz.query_current_context` function.

.. release:: 0.8.1
    :date: 2018-04-23

    .. change:: fixed
        :tags: API

        Added missing argument to :func:`wiz.query_current_context` function.

.. release:: 0.8.0
    :date: 2018-04-23

    .. change:: new
        :tags: documentation

        Added ``tutorial`` section to documentation, including a guide for
        project registries, as well as some introduction into
        :ref:`registry` and :ref:`definition`.
        Additional :ref:`guidelines` and "tools" sections have been added to
        provide help for developers.

.. release:: 0.7.1
    :date: 2018-04-20

    .. change:: fixed
        :tags: command-line

        Fixed :func:`wiz.command_line.main` to correctly launch a command within
        a resolved context as follow::

            wiz use baselight-nuke -- nukex

    .. change:: fixed
        :tags: debug

        Changed :func:`wiz.history.get` to correctly set the timestamp to the
        history mapping returned.

.. release:: 0.7.0
    :date: 2018-04-18

    .. change:: fixed
        :tags: resolver

        When a node was removed from the graph due to a requirement conflict
        which prioritize another version of the same package identifier, the
        link was not re-assigned to the correct node. This could lead to
        an incorrect priority mapping computation which would alter the package
        order resolution.

        Changed :meth:`wiz.graph.Resolver.resolve_conflicts` to update the link
        when a conflicted node is removed.

.. release:: 0.6.0
    :date: 2018-04-18

    .. change:: fixed
        :tags: registry

        Changed :func:`wiz.registry.fetch` to return the registry folders is the
        correct order so that package definitions from the secondary registry h
        ave priority order package definitions from the primary registry.

.. release:: 0.5.0
    :date: 2018-04-17

    .. change:: changed
        :tags: command-line

        Moved :option:`--definition-search-paths <wiz --registry>`,
        to the top level parser so that registries could be modified for every
        sub-commands.

.. release:: 0.4.0
    :date: 2018-04-17

    .. change:: changed
        :tags: registry

        Changed :func:`wiz.registry.get_defaults` to return two global registry
        folders instead of one: The "primary" registry would store all vanilla
        package definitions and the "secondary" one would store all package
        combinations that need to be available globally.

.. release:: 0.3.0
    :date: 2018-04-16

    .. change:: new
        :tags: debug

        Added :mod:`wiz.history` to let the user record a compressed file
        with all necessary information about the API calls executed and the
        context in which it was executed (wiz version, username, hostname, time,
        timezone,...).

        :func:`wiz.history.record_action` is called within precise functions
        with a clear action identifier and relevant arguments to record all
        major steps of the graph resolution process (including errors).

    .. change:: new
        :tags: command-line, debug

        Added :option:`--record <wiz --record>` command line option to export a
        dump file with :mod:`recorded history <wiz.history>`.

    .. change:: changed
        :tags: debug

        Changed :meth:`wiz.graph.Resolver.compute_packages` to traverse package
        requirements in `Breadth First Mode`_ in order to include packages with
        highest priority first in the graph. This allow for better error message
        (incorrect package with higher priority will fail before a less
        important one), and a more logical order for actions recorded in
        :mod:`recorded history <wiz.history>`.

        .. _Breadth First Mode: https://en.wikipedia.org/wiki/Breadth-first_search

.. release:: 0.2.0
    :date: 2018-03-30

    .. change:: changed
        :tags: deployment

        Remove :file:`package.py` script as the tool will be installed as a
        library within a python context instead.

.. release:: 0.1.0
    :date: 2018-03-30

    .. change:: new
        :tags: command-line

        Added :mod:`wiz.command_line` to initiate the command line tool.

    .. change:: new
        :tags: API

        Added :mod:`wiz` to expose high-level API.

    .. change:: new
        :tags: API

        Added :mod:`wiz.definition` to discover and create
        :class:`~wiz.definition.Definition` instances from registry folder.

    .. change:: new
        :tags: API

        Added :mod:`wiz.package` to extract :class:`~wiz.package.Package`
        instances from a :class:`~wiz.definition.Definition` instance and
        resolve a context mapping with initial environment mapping.

    .. change:: new
        :tags: API

        Added :mod:`wiz.graph` to resolve package requirement graph(s) and
        extract ordered :class:`~wiz.package.Package` instances.

    .. change:: new
        :tags: API

        Added :mod:`wiz.registry` to query available registry folders.

    .. change:: new
        :tags: API

        Added :mod:`wiz.spawn` to start a :term:`shell <Unix Shell>` or execute
        a command within a resolved environment mapping.

    .. change:: new
        :tags: API

        Added :mod:`wiz.system` to query current system information and filter
        fetched definitions accordingly.

    .. change:: new
        :tags: API

        Added :mod:`wiz.filesystem` to deal with files and folders creation.

    .. change:: new
        :tags: internal

        Added :mod:`wiz.mapping` to define immutable serializable mapping object
        used by :class:`~wiz.definition.Definition` and
        :class:`~wiz.package.Package` instances.

    .. change:: new
        :tags: API

        Added :mod:`wiz.symbol` to regroup all Wiz symbols.

    .. change:: new
        :tags: API

        Added :mod:`wiz.exception` to regroup all Wiz exceptions.
