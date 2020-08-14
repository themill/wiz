.. _environment_variables:

*********************
Environment variables
*********************

Environment variables directly defined or referenced by this package.

.. envvar:: INSTALL_LOCATION

    Environment variable used within a Wiz definition environment to refer to
    the install location of a package.

    .. seealso:: :ref:`definition/install_location`

.. envvar:: INSTALL_ROOT

    Environment variable used within a Wiz definition environment to refer to
    the root of the install location of a package.

    .. seealso:: :ref:`definition/install_root`

.. envvar:: WIZ_CONTEXT

    Environment variable automatically added to a resolved context created by
    :func:`wiz.resolve_context`. It contains the encoded context that can
    be :func:`discovered <wiz.discover_context>` from within the context.
