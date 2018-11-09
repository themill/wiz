.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

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

    .. change:: changed
        :tags: command-line

        Updated :mod:`wiz.command_line` to use :mod:`click` instead of
        :mod:`argparse` in order to improve code maintainability.

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
        :tags: API, command-line

        Updated :func:`wiz.spawn.execute` to substitute environment variables
        within command elements before the execution process. User can then
        use environment variables in command, such as::

            >>> wiz use python -- echo \$PIP_CONFIG_FILE

    .. change:: changed
        :tags: API

        Moved :func:`wiz.package.initiate_environ` to
        :func:`wiz.environ.initiate`.

    .. change:: changed
        :tags: API

        Moved :func:`wiz.package.sanitise_environ_mapping` to
        :func:`wiz.environ.sanitise`.

    .. change:: changed
        :tags: API

        Updated :mod:`wiz.fetch_definition_mapping` to add the *requests*
        argument which can influence the definition research.

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

        .. seealso:: :ref:`installing_definitions`

    .. change:: new
        :tags: definition

        Added optional :ref:`group <definition/group>` keyword to definition
        schema, which can be used to define where in the hierarchy of a
        :term:`VCS Registry` a definition will be installed (e.g. "python",
        "maya").

    .. change:: new
        :tags: definition

        Added optional :ref:`install-location <definition/install_location>`
        keyword to definition schema to indicate the root location of a package
        data.

    .. change:: new
        :tags: API

        Added :func:`wiz.install_definitions_to_path` and
        :func:`wiz.install_definitions_to_vcs` to install one or several
        definition files to a :term:`Local Registry` or a :term:`VCS Registry`.

    .. change:: new
        :tags: API

        Added :func:`wiz.registry.install_to_path` and
        :func:`wiz.registry.install_to_vcs` to install a definition instance
        to a :term:`Local Registry` or a :term:`VCS Registry`.

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

        Added :ref:`installing_definitions` section.

    .. change:: new
        :tags: documentation

        Added :ref:`tutorial/install/qip` section to tutorial.

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
        the 'auto-use' keyword is displayed at a logical position in the
        serialized definition and package instances.

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

        Added optional 'constraints' keyword to definition schema which
        indicates a list of package requirements which should be used to resolve
        a context only if another package with the same definition identifier is
        required.

    .. change:: new
        :tags: definition

        Added optional 'auto-use' keyword to definition schema which indicates
        whether corresponding package should be used implicitly to resolve
        context. Default is False.

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
        yield potential errors in a definition data following a
        :term:`JSON Schema`.

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

        Added :ref:`tutorial` section to documentation, including a guide for
        :ref:`tutorial/project`, as well as some introduction into
        :ref:`registry` and :ref:`definition`.
        Additonal :ref:`guidelines` and :ref:`tools` sections have been added to
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

        Moved :option:`--definition-search-paths <wiz --definition-search-paths>`,
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
