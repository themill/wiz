.. _release/release_notes:

*************
Release Notes
*************

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

        Changed the :option:`view <wiz view request>` command line option to
        only display the full definition if the request is identified as a
        package definition. If the request is identified as a command, only the
        corresponding definition identifier is displayed.

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
