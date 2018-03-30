.. _release/release_notes:

*************
Release Notes
*************

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
